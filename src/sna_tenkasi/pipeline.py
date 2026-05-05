from __future__ import annotations

import argparse

import pandas as pd

from .analysis import (
    compute_centrality_metrics,
    compute_network_statistics,
    correlate_rating_and_centrality,
    detect_communities,
    persist_analysis_outputs,
    save_json,
    run_link_prediction,
)
from .collector import run_collection
from .config import EXPORTS_DIR, OUTPUTS_DIR, ProjectConfig, ensure_directories
from .graphs import (
    build_edges_dataframe,
    build_place_place_graph,
    graph_to_nodes_dataframe,
    build_user_place_graph,
    build_user_user_graph,
)
from .neo4j_export import export_neo4j_csvs
from .neo4j_export import import_into_neo4j


def load_core_data(config: ProjectConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not config.places_csv.exists() or not config.reviews_csv.exists():
        raise FileNotFoundError(
            "Structured datasets are missing. Run the collector first or use --collect."
        )
    return pd.read_csv(config.places_csv), pd.read_csv(config.reviews_csv)


def generate_insights(
    places_df: pd.DataFrame,
    place_metrics_df: pd.DataFrame,
    user_metrics_df: pd.DataFrame,
    place_stats: dict,
    rating_correlation: dict[str, float],
) -> dict:
    top_place = place_metrics_df.nsmallest(1, "average_rank").iloc[0].to_dict() if not place_metrics_df.empty else {}
    top_bridge = (
        place_metrics_df.sort_values(by="betweenness_centrality", ascending=False).head(1).iloc[0].to_dict()
        if not place_metrics_df.empty
        else {}
    )
    top_user = user_metrics_df.nsmallest(1, "average_rank").iloc[0].to_dict() if not user_metrics_df.empty else {}

    high_rated = places_df[["place_name", "rating", "total_user_ratings"]].sort_values(
        by=["rating", "total_user_ratings"], ascending=[False, False]
    ).head(10)
    highly_connected = place_metrics_df[["label", "degree_centrality", "pagerank"]].sort_values(
        by=["degree_centrality", "pagerank"], ascending=[False, False]
    ).head(10)

    return {
        "most_influential_place": top_place,
        "bridge_place": top_bridge,
        "most_central_user": top_user,
        "network_summary": place_stats,
        "rating_centrality_correlation": rating_correlation,
        "highly_rated_places": high_rated.to_dict(orient="records"),
        "highly_connected_places": highly_connected.to_dict(orient="records"),
    }


def run_pipeline(
    collect: bool = False,
    export_neo4j: bool = False,
    import_neo4j: bool = False,
    config: ProjectConfig | None = None,
) -> None:
    config = config or ProjectConfig()
    ensure_directories()

    if collect:
        run_collection(config)

    places_df, reviews_df = load_core_data(config)
    user_place_graph = build_user_place_graph(places_df, reviews_df)
    place_graph = build_place_place_graph(places_df, reviews_df)
    user_graph = build_user_user_graph(reviews_df)

    edges_df = build_edges_dataframe(user_place_graph, place_graph, user_graph)
    edges_df.to_csv(config.edges_csv, index=False)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    user_place_edges_df = edges_df[edges_df["relationship_type"] == "reviewed"].copy()
    place_edges_df = edges_df[edges_df["relationship_type"] == "co_reviewed_place"].copy()
    user_edges_df = edges_df[edges_df["relationship_type"] == "co_reviewed_user"].copy()

    graph_to_nodes_dataframe(user_place_graph, "user_place_bipartite").to_csv(
        EXPORTS_DIR / "user_place_nodes.csv", index=False
    )
    graph_to_nodes_dataframe(place_graph, "place_network").to_csv(
        EXPORTS_DIR / "place_network_nodes.csv", index=False
    )
    graph_to_nodes_dataframe(user_graph, "user_network").to_csv(
        EXPORTS_DIR / "user_network_nodes.csv", index=False
    )
    user_place_edges_df.to_csv(EXPORTS_DIR / "user_place_edges.csv", index=False)
    place_edges_df.to_csv(EXPORTS_DIR / "place_network_edges.csv", index=False)
    user_edges_df.to_csv(EXPORTS_DIR / "user_network_edges.csv", index=False)

    place_metrics_df = compute_centrality_metrics(place_graph)
    user_metrics_df = compute_centrality_metrics(user_graph)
    place_stats = compute_network_statistics(place_graph)
    user_stats = compute_network_statistics(user_graph)
    place_communities = detect_communities(place_graph)
    user_communities = detect_communities(user_graph)
    link_predictions_df = run_link_prediction(place_graph)
    rating_correlation = correlate_rating_and_centrality(places_df, place_metrics_df)

    for node, pagerank in place_metrics_df.set_index("node")["pagerank"].to_dict().items():
        if node in place_graph.nodes:
            place_graph.nodes[node]["pagerank"] = pagerank
    for node, pagerank in user_metrics_df.set_index("node")["pagerank"].to_dict().items():
        if node in user_graph.nodes:
            user_graph.nodes[node]["pagerank"] = pagerank

    persist_analysis_outputs("place_network", place_graph, places_df, place_metrics_df, place_stats, place_communities, link_predictions_df)
    persist_analysis_outputs("user_network", user_graph, places_df, user_metrics_df, user_stats, user_communities)

    save_json(user_stats, OUTPUTS_DIR / "metrics" / "user_network_stats.json")
    insights = generate_insights(places_df, place_metrics_df, user_metrics_df, place_stats, rating_correlation)
    save_json(insights, OUTPUTS_DIR / "insights.json")

    if export_neo4j or import_neo4j:
        place_nodes_df = graph_to_nodes_dataframe(place_graph, "place_network")
        user_nodes_df = graph_to_nodes_dataframe(user_graph, "user_network")
        export_neo4j_csvs(
            places_df=places_df,
            reviews_df=reviews_df,
            place_nodes_df=place_nodes_df,
            user_nodes_df=user_nodes_df,
            place_edges_df=place_edges_df,
            user_edges_df=user_edges_df,
            user_place_edges_df=user_place_edges_df,
        )
    if import_neo4j:
        import_into_neo4j()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Tenkasi tourism SNA pipeline.")
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Fetch fresh data from Google Places before analysis.",
    )
    parser.add_argument(
        "--export-neo4j",
        action="store_true",
        help="Generate Neo4j-ready CSV exports and Cypher import script.",
    )
    parser.add_argument(
        "--import-neo4j",
        action="store_true",
        help="Import the generated graph data into Neo4j using NEO4J_* environment variables.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(
        collect=args.collect,
        export_neo4j=args.export_neo4j,
        import_neo4j=args.import_neo4j,
    )
    print("Pipeline completed. Outputs saved under data/ and outputs/.")


if __name__ == "__main__":
    main()
