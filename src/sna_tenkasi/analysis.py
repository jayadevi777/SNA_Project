from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from networkx.readwrite import json_graph
import pandas as pd

from .config import COMMUNITIES_DIR, EXPORTS_DIR, GRAPHS_DIR, LINK_PREDICTION_DIR, METRICS_DIR, PLOTS_DIR


METRIC_COLUMNS = [
    "degree_centrality",
    "betweenness_centrality",
    "closeness_centrality",
    "eigenvector_centrality",
    "katz_centrality",
    "pagerank",
    "hits_hub",
    "hits_authority",
]


def _safe_metric(default_nodes: list[str], func, fallback: float = 0.0) -> dict[str, float]:
    try:
        values = func()
        return {node: float(values.get(node, fallback)) for node in default_nodes}
    except Exception:
        return {node: fallback for node in default_nodes}


def compute_centrality_metrics(graph: nx.Graph) -> pd.DataFrame:
    if graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=["node", *METRIC_COLUMNS])

    nodes = list(graph.nodes())
    directed_graph = nx.DiGraph()
    directed_graph.add_nodes_from(graph.nodes(data=True))
    for left, right, attrs in graph.edges(data=True):
        directed_graph.add_edge(left, right, **attrs)
        directed_graph.add_edge(right, left, **attrs)

    metrics = {
        "degree_centrality": nx.degree_centrality(graph),
        "betweenness_centrality": nx.betweenness_centrality(graph, weight="weight", normalized=True),
        "closeness_centrality": nx.closeness_centrality(graph, distance=None),
        "eigenvector_centrality": _safe_metric(
            nodes, lambda: nx.eigenvector_centrality_numpy(graph, weight="weight")
        ),
        "katz_centrality": _safe_metric(
            nodes, lambda: nx.katz_centrality_numpy(graph, weight="weight", alpha=0.005, beta=1.0)
        ),
        "pagerank": _safe_metric(nodes, lambda: nx.pagerank(directed_graph, weight="weight")),
    }

    try:
        hubs, authorities = nx.hits(directed_graph, max_iter=200, normalized=True)
    except Exception:
        hubs = {node: 0.0 for node in nodes}
        authorities = {node: 0.0 for node in nodes}

    metrics["hits_hub"] = hubs
    metrics["hits_authority"] = authorities

    rows = []
    for node in nodes:
        row = {"node": node, **{metric: float(values.get(node, 0.0)) for metric, values in metrics.items()}}
        row["label"] = graph.nodes[node].get("label", node)
        row["node_type"] = graph.nodes[node].get("node_type", "unknown")
        rows.append(row)

    results = pd.DataFrame(rows)
    results["average_rank"] = results[METRIC_COLUMNS].rank(ascending=False, method="min").mean(axis=1)
    return results.sort_values(by="average_rank")


def compute_network_statistics(graph: nx.Graph) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph) if graph.number_of_nodes() > 1 else 0.0,
        "average_clustering": nx.average_clustering(graph, weight="weight") if graph.number_of_nodes() > 1 else 0.0,
        "connected_components": nx.number_connected_components(graph) if graph.number_of_nodes() else 0,
    }

    if graph.number_of_nodes():
        component_sizes = sorted((len(component) for component in nx.connected_components(graph)), reverse=True)
        stats["largest_component_size"] = component_sizes[0]
        giant_nodes = max(nx.connected_components(graph), key=len)
        giant_graph = graph.subgraph(giant_nodes).copy()
        stats["average_shortest_path_length"] = (
            nx.average_shortest_path_length(giant_graph) if giant_graph.number_of_nodes() > 1 else 0.0
        )
    else:
        stats["largest_component_size"] = 0
        stats["average_shortest_path_length"] = 0.0

    degrees = [degree for _, degree in graph.degree()]
    degree_counter = Counter(degrees)
    stats["degree_distribution"] = dict(sorted(degree_counter.items()))
    stats["power_law_alpha"] = estimate_power_law_alpha(degrees)
    return stats


def estimate_power_law_alpha(degrees: list[int]) -> float | None:
    positive = [degree for degree in degrees if degree > 0]
    if len(positive) < 2:
        return None
    xmin = min(positive)
    denominator = sum(math.log(degree / (xmin - 0.5)) for degree in positive if degree > xmin - 0.5)
    if denominator <= 0:
        return None
    return 1 + (len(positive) / denominator)


def detect_communities(graph: nx.Graph) -> dict[str, list[list[str]]]:
    communities: dict[str, list[list[str]]] = {"girvan_newman": [], "louvain": []}
    if graph.number_of_nodes() < 2 or graph.number_of_edges() == 0:
        return communities

    girvan_generator = nx.community.girvan_newman(graph)
    try:
        best_partition = next(girvan_generator)
        communities["girvan_newman"] = [sorted(group) for group in best_partition]
    except StopIteration:
        communities["girvan_newman"] = []

    louvain_method = getattr(nx.community, "louvain_communities", None)
    if callable(louvain_method):
        communities["louvain"] = [sorted(group) for group in louvain_method(graph, weight="weight", seed=42)]
    else:
        communities["louvain"] = [
            sorted(group) for group in nx.community.greedy_modularity_communities(graph, weight="weight")
        ]
    return communities


def run_link_prediction(graph: nx.Graph, top_k: int = 20) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    candidates = list(nx.non_edges(graph))
    common_neighbors = {(u, v): len(list(nx.common_neighbors(graph, u, v))) for u, v in candidates}
    jaccard_scores = {(u, v): score for u, v, score in nx.jaccard_coefficient(graph, candidates)}
    adamic_scores = {(u, v): score for u, v, score in nx.adamic_adar_index(graph, candidates)}

    for left, right in candidates:
        rows.append(
            {
                "node1": left,
                "node2": right,
                "common_neighbors": common_neighbors[(left, right)],
                "jaccard_coefficient": jaccard_scores.get((left, right), 0.0),
                "adamic_adar": adamic_scores.get((left, right), 0.0),
            }
        )

    results = pd.DataFrame(rows)
    if results.empty:
        return results

    results["combined_score"] = (
        results["common_neighbors"].rank(pct=True)
        + results["jaccard_coefficient"].rank(pct=True)
        + results["adamic_adar"].rank(pct=True)
    ) / 3
    return results.sort_values(by="combined_score", ascending=False).head(top_k)


def correlate_rating_and_centrality(places_df: pd.DataFrame, place_metrics_df: pd.DataFrame) -> dict[str, float]:
    metrics_df = place_metrics_df[["node", "pagerank", "betweenness_centrality", "degree_centrality"]].copy()
    metrics_df["place_id"] = metrics_df["node"].str.replace("place::", "", regex=False)
    merged = places_df.merge(metrics_df.drop(columns=["node"]), on="place_id", how="left")
    metrics = ["pagerank", "betweenness_centrality", "degree_centrality"]
    return {
        metric: float(merged["rating"].corr(merged[metric])) if merged[metric].notna().sum() > 1 else 0.0
        for metric in metrics
    }


def export_graph(graph: nx.Graph, output_path: Path) -> None:
    nx.write_gexf(graph, output_path)


def save_degree_distribution_plot(graph: nx.Graph, title: str, output_path: Path) -> None:
    degrees = [degree for _, degree in graph.degree()]
    plt.figure(figsize=(8, 5))
    plt.hist(degrees, bins=min(15, max(5, len(set(degrees)) or 5)), color="#1f77b4", edgecolor="white")
    plt.title(title)
    plt.xlabel("Degree")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_centrality_plot(metrics_df: pd.DataFrame, title: str, output_path: Path, top_k: int = 10) -> None:
    subset = metrics_df.nsmallest(top_k, "average_rank")
    plt.figure(figsize=(10, 6))
    plt.barh(subset["label"], subset["pagerank"], color="#ff7f0e")
    plt.title(title)
    plt.xlabel("PageRank")
    plt.ylabel("Node")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_metric_bar_plot(
    metrics_df: pd.DataFrame, metric: str, title: str, output_path: Path, top_k: int = 12
) -> None:
    if metrics_df.empty or metric not in metrics_df.columns:
        return
    subset = metrics_df.nlargest(top_k, metric)
    plt.figure(figsize=(10, 6))
    plt.barh(subset["label"], subset[metric], color=plt.cm.viridis(range(len(subset))))
    plt.gca().invert_yaxis()
    plt.title(title)
    plt.xlabel(metric.replace("_", " ").title())
    plt.ylabel("Node")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_network_plot(graph: nx.Graph, title: str, output_path: Path, color_by: str = "pagerank") -> None:
    plt.figure(figsize=(10, 8))
    if graph.number_of_nodes() == 0:
        plt.title(title)
        plt.savefig(output_path, dpi=200)
        plt.close()
        return

    layout = nx.spring_layout(graph, seed=42, weight="weight")
    values = []
    for node in graph.nodes:
        values.append(graph.nodes[node].get(color_by, graph.degree(node)))

    nx.draw_networkx(
        graph,
        pos=layout,
        node_size=180,
        node_color=values,
        cmap=plt.cm.plasma,
        with_labels=False,
        edge_color="#b9c3d1",
        alpha=0.85,
    )
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_rating_correlation_plot(
    places_df: pd.DataFrame, metrics_df: pd.DataFrame, metric: str, output_path: Path
) -> None:
    if places_df.empty or metrics_df.empty or metric not in metrics_df.columns:
        return
    merged = metrics_df.copy()
    merged["place_id"] = merged["node"].str.replace("place::", "", regex=False)
    merged = places_df.merge(merged[["place_id", metric, "label"]], on="place_id", how="inner")
    merged["rating"] = pd.to_numeric(merged["rating"], errors="coerce")
    merged = merged.dropna(subset=["rating", metric])
    if merged.empty:
        return
    plt.figure(figsize=(8, 6))
    plt.scatter(merged["rating"], merged[metric], c=merged[metric], cmap="plasma", s=60, alpha=0.8)
    plt.title(f"Rating vs {metric.replace('_', ' ').title()}")
    plt.xlabel("Google Rating")
    plt.ylabel(metric.replace("_", " ").title())
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_category_distribution_plot(places_df: pd.DataFrame, output_path: Path, top_k: int = 10) -> None:
    if places_df.empty or "category" not in places_df.columns:
        return
    counts = (
        places_df.fillna({"category": "unknown"})
        .groupby("category")
        .size()
        .sort_values(ascending=False)
        .head(top_k)
    )
    if counts.empty:
        return
    plt.figure(figsize=(10, 6))
    plt.barh(counts.index.astype(str), counts.values, color=plt.cm.cividis(range(len(counts))))
    plt.gca().invert_yaxis()
    plt.title("Top Place Categories")
    plt.xlabel("Count")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_community_size_plot(communities: dict[str, list[list[str]]], output_path: Path) -> None:
    louvain = communities.get("louvain", [])
    if not louvain:
        return
    sizes = [len(group) for group in louvain]
    plt.figure(figsize=(8, 5))
    plt.bar(range(1, len(sizes) + 1), sizes, color="#0f766e")
    plt.title("Louvain Community Sizes")
    plt.xlabel("Community")
    plt.ylabel("Nodes")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_json(data: Any, output_path: Path) -> None:
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def save_graph_json(graph: nx.Graph, output_path: Path) -> None:
    graph_payload = json_graph.node_link_data(graph)
    output_path.write_text(json.dumps(graph_payload, indent=2, ensure_ascii=False))


def save_metric_summary(metrics_df: pd.DataFrame, output_path: Path, top_k: int = 10) -> None:
    summary: dict[str, list[dict[str, Any]]] = {}
    if metrics_df.empty:
        save_json(summary, output_path)
        return
    for metric in METRIC_COLUMNS:
        summary[metric] = (
            metrics_df.nlargest(top_k, metric)[["label", "node", metric]].to_dict(orient="records")
            if metric in metrics_df.columns
            else []
        )
    save_json(summary, output_path)


def persist_analysis_outputs(
    graph_name: str,
    graph: nx.Graph,
    places_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    stats: dict[str, Any],
    communities: dict[str, list[list[str]]],
    predictions_df: pd.DataFrame | None = None,
) -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    COMMUNITIES_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LINK_PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    metrics_path = METRICS_DIR / f"{graph_name}_metrics.csv"
    stats_path = METRICS_DIR / f"{graph_name}_stats.json"
    community_path = COMMUNITIES_DIR / f"{graph_name}_communities.json"
    graph_path = GRAPHS_DIR / f"{graph_name}.gexf"
    graph_json_path = GRAPHS_DIR / f"{graph_name}.json"

    metrics_df.to_csv(metrics_path, index=False)
    save_json(stats, stats_path)
    save_json(communities, community_path)
    export_graph(graph, graph_path)
    save_graph_json(graph, graph_json_path)
    save_metric_summary(metrics_df, METRICS_DIR / f"{graph_name}_metric_summary.json")
    save_degree_distribution_plot(graph, f"{graph_name.title()} Degree Distribution", PLOTS_DIR / f"{graph_name}_degree_distribution.png")
    save_centrality_plot(metrics_df, f"{graph_name.title()} PageRank Leaders", PLOTS_DIR / f"{graph_name}_centrality.png")
    save_network_plot(graph, f"{graph_name.title()} Network", PLOTS_DIR / f"{graph_name}_network.png")
    save_metric_bar_plot(metrics_df, "betweenness_centrality", f"{graph_name.title()} Betweenness Leaders", PLOTS_DIR / f"{graph_name}_betweenness.png")
    save_metric_bar_plot(metrics_df, "closeness_centrality", f"{graph_name.title()} Closeness Leaders", PLOTS_DIR / f"{graph_name}_closeness.png")
    save_metric_bar_plot(metrics_df, "degree_centrality", f"{graph_name.title()} Degree Leaders", PLOTS_DIR / f"{graph_name}_degree_top.png")
    save_community_size_plot(communities, PLOTS_DIR / f"{graph_name}_community_sizes.png")

    if graph_name == "place_network":
        save_rating_correlation_plot(places_df, metrics_df, "pagerank", PLOTS_DIR / f"{graph_name}_rating_vs_pagerank.png")
        save_rating_correlation_plot(places_df, metrics_df, "betweenness_centrality", PLOTS_DIR / f"{graph_name}_rating_vs_betweenness.png")
        save_category_distribution_plot(places_df, PLOTS_DIR / "place_categories.png")

    if predictions_df is not None:
        predictions_df.to_csv(LINK_PREDICTION_DIR / f"{graph_name}_predictions.csv", index=False)
