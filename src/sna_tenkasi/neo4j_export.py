from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from .config import NEO4J_DIR


def export_neo4j_csvs(
    places_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    place_nodes_df: pd.DataFrame,
    user_nodes_df: pd.DataFrame,
    place_edges_df: pd.DataFrame,
    user_edges_df: pd.DataFrame,
    user_place_edges_df: pd.DataFrame,
) -> dict[str, Path]:
    NEO4J_DIR.mkdir(parents=True, exist_ok=True)

    place_nodes = places_df.copy()
    place_nodes["node_id:ID(Place)"] = place_nodes["place_id"].astype(str)
    place_nodes["name"] = place_nodes["place_name"]
    place_nodes[":LABEL"] = "Place"
    place_nodes = place_nodes[
        [
            "node_id:ID(Place)",
            "name",
            "category",
            "rating",
            "total_user_ratings",
            "formatted_address",
            "google_maps_url",
            ":LABEL",
        ]
    ]

    user_nodes = user_nodes_df.copy()
    if not user_nodes.empty:
        user_nodes["node_id:ID(User)"] = user_nodes["node"].str.replace("user::", "", regex=False)
        user_nodes["name"] = user_nodes["label"]
        user_nodes[":LABEL"] = "User"
        user_nodes = user_nodes[["node_id:ID(User)", "name", ":LABEL"]].drop_duplicates()

    reviewed_edges = reviews_df.copy()
    if not reviewed_edges.empty:
        reviewed_edges[":START_ID(User)"] = reviewed_edges["user_name"].map(
            lambda name: "".join(ch.lower() if ch.isalnum() else "_" for ch in str(name).strip()).strip("_") or "anonymous"
        )
        reviewed_edges[":END_ID(Place)"] = reviewed_edges["place_id"].astype(str)
        reviewed_edges[":TYPE"] = "REVIEWED"
        reviewed_edges = reviewed_edges[
            [":START_ID(User)", ":END_ID(Place)", "rating", "review_text", ":TYPE"]
        ]

    place_edges = place_edges_df.copy()
    if not place_edges.empty:
        place_edges[":START_ID(Place)"] = place_edges["node1"].str.replace("place::", "", regex=False)
        place_edges[":END_ID(Place)"] = place_edges["node2"].str.replace("place::", "", regex=False)
        place_edges[":TYPE"] = "CO_VISITED"
        place_edges = place_edges[[":START_ID(Place)", ":END_ID(Place)", "weight", ":TYPE"]]

    user_edges = user_edges_df.copy()
    if not user_edges.empty:
        user_edges[":START_ID(User)"] = user_edges["node1"].str.replace("user::", "", regex=False)
        user_edges[":END_ID(User)"] = user_edges["node2"].str.replace("user::", "", regex=False)
        user_edges[":TYPE"] = "SIMILAR_USER"
        user_edges = user_edges[[":START_ID(User)", ":END_ID(User)", "weight", ":TYPE"]]

    outputs = {
        "place_nodes": NEO4J_DIR / "place_nodes.csv",
        "user_nodes": NEO4J_DIR / "user_nodes.csv",
        "reviewed_edges": NEO4J_DIR / "reviewed_edges.csv",
        "place_edges": NEO4J_DIR / "place_edges.csv",
        "user_edges": NEO4J_DIR / "user_edges.csv",
        "import_cypher": NEO4J_DIR / "import.cypher",
    }

    place_nodes.to_csv(outputs["place_nodes"], index=False)
    user_nodes.to_csv(outputs["user_nodes"], index=False)
    reviewed_edges.to_csv(outputs["reviewed_edges"], index=False)
    place_edges.to_csv(outputs["place_edges"], index=False)
    user_edges.to_csv(outputs["user_edges"], index=False)

    outputs["import_cypher"].write_text(
        "\n".join(
            [
                "LOAD CSV WITH HEADERS FROM 'file:///place_nodes.csv' AS row",
                "MERGE (p:Place {place_id: row.`node_id:ID(Place)`})",
                "SET p.name = row.name, p.category = row.category, p.rating = toFloat(row.rating), p.total_user_ratings = toInteger(row.total_user_ratings), p.formatted_address = row.formatted_address, p.google_maps_url = row.google_maps_url;",
                "",
                "LOAD CSV WITH HEADERS FROM 'file:///user_nodes.csv' AS row",
                "MERGE (u:User {user_id: row.`node_id:ID(User)`})",
                "SET u.name = row.name;",
                "",
                "LOAD CSV WITH HEADERS FROM 'file:///reviewed_edges.csv' AS row",
                "MATCH (u:User {user_id: row.`:START_ID(User)`})",
                "MATCH (p:Place {place_id: row.`:END_ID(Place)`})",
                "MERGE (u)-[r:REVIEWED]->(p)",
                "SET r.rating = toFloat(row.rating), r.review_text = row.review_text;",
                "",
                "LOAD CSV WITH HEADERS FROM 'file:///place_edges.csv' AS row",
                "MATCH (p1:Place {place_id: row.`:START_ID(Place)`})",
                "MATCH (p2:Place {place_id: row.`:END_ID(Place)`})",
                "MERGE (p1)-[r:CO_VISITED]->(p2)",
                "SET r.weight = toInteger(row.weight);",
                "",
                "LOAD CSV WITH HEADERS FROM 'file:///user_edges.csv' AS row",
                "MATCH (u1:User {user_id: row.`:START_ID(User)`})",
                "MATCH (u2:User {user_id: row.`:END_ID(User)`})",
                "MERGE (u1)-[r:SIMILAR_USER]->(u2)",
                "SET r.weight = toInteger(row.weight);",
            ]
        )
    )

    return outputs


def neo4j_env_config() -> dict[str, str]:
    return {
        "uri": os.getenv("NEO4J_URI", ""),
        "username": os.getenv("NEO4J_USERNAME", ""),
        "password": os.getenv("NEO4J_PASSWORD", ""),
        "database": os.getenv("NEO4J_DATABASE", "neo4j"),
    }


def import_into_neo4j(*_args, **_kwargs) -> None:
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise RuntimeError("Neo4j runtime import requires the `neo4j` package.") from exc

    config = neo4j_env_config()
    if not config["uri"] or not config["username"] or not config["password"]:
        raise RuntimeError("Missing NEO4J_URI, NEO4J_USERNAME, or NEO4J_PASSWORD.")

    place_nodes_path = NEO4J_DIR / "place_nodes.csv"
    user_nodes_path = NEO4J_DIR / "user_nodes.csv"
    reviewed_edges_path = NEO4J_DIR / "reviewed_edges.csv"
    place_edges_path = NEO4J_DIR / "place_edges.csv"
    user_edges_path = NEO4J_DIR / "user_edges.csv"
    for path in [place_nodes_path, user_nodes_path, reviewed_edges_path, place_edges_path, user_edges_path]:
        if not path.exists():
            raise RuntimeError(f"Missing Neo4j export file: {path.name}. Run the pipeline with --export-neo4j first.")

    driver = GraphDatabase.driver(config["uri"], auth=(config["username"], config["password"]))
    try:
        with driver.session(database=config["database"]) as session:
            session.run("MATCH (u:User)-[r]-() DELETE r")
            session.run("MATCH (p:Place)-[r]-() DELETE r")
            session.run("MATCH (u:User) DELETE u")
            session.run("MATCH (p:Place) DELETE p")
            session.run("CREATE CONSTRAINT place_id_unique IF NOT EXISTS FOR (p:Place) REQUIRE p.place_id IS UNIQUE")
            session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")

            place_nodes = pd.read_csv(place_nodes_path).fillna("").to_dict(orient="records")
            user_nodes = pd.read_csv(user_nodes_path).fillna("").to_dict(orient="records")
            reviewed_edges = pd.read_csv(reviewed_edges_path).fillna("").to_dict(orient="records")
            place_edges = pd.read_csv(place_edges_path).fillna("").to_dict(orient="records")
            user_edges = pd.read_csv(user_edges_path).fillna("").to_dict(orient="records")

            session.run(
                """
                UNWIND $rows AS row
                MERGE (p:Place {place_id: row.`node_id:ID(Place)`})
                SET p.name = row.name,
                    p.category = row.category,
                    p.rating = CASE WHEN row.rating = '' THEN NULL ELSE toFloat(row.rating) END,
                    p.total_user_ratings = CASE WHEN row.total_user_ratings = '' THEN NULL ELSE toInteger(row.total_user_ratings) END,
                    p.formatted_address = row.formatted_address,
                    p.google_maps_url = row.google_maps_url
                """,
                rows=place_nodes,
            )
            session.run(
                """
                UNWIND $rows AS row
                MERGE (u:User {user_id: row.`node_id:ID(User)`})
                SET u.name = row.name
                """,
                rows=user_nodes,
            )
            session.run(
                """
                UNWIND $rows AS row
                MATCH (u:User {user_id: row.`:START_ID(User)`})
                MATCH (p:Place {place_id: row.`:END_ID(Place)`})
                MERGE (u)-[r:REVIEWED]->(p)
                SET r.rating = CASE WHEN row.rating = '' THEN NULL ELSE toFloat(row.rating) END,
                    r.review_text = row.review_text
                """,
                rows=reviewed_edges,
            )
            session.run(
                """
                UNWIND $rows AS row
                MATCH (p1:Place {place_id: row.`:START_ID(Place)`})
                MATCH (p2:Place {place_id: row.`:END_ID(Place)`})
                MERGE (p1)-[r:CO_VISITED]->(p2)
                SET r.weight = CASE WHEN row.weight = '' THEN 1 ELSE toInteger(row.weight) END
                """,
                rows=place_edges,
            )
            session.run(
                """
                UNWIND $rows AS row
                MATCH (u1:User {user_id: row.`:START_ID(User)`})
                MATCH (u2:User {user_id: row.`:END_ID(User)`})
                MERGE (u1)-[r:SIMILAR_USER]->(u2)
                SET r.weight = CASE WHEN row.weight = '' THEN 1 ELSE toInteger(row.weight) END
                """,
                rows=user_edges,
            )
    finally:
        driver.close()
