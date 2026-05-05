from __future__ import annotations

from collections import defaultdict
from itertools import combinations

import networkx as nx
import pandas as pd


def create_user_identifier(name: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    return f"user::{normalized.strip('_') or 'anonymous'}"


def _infer_taluk(value: str) -> str:
    text = str(value or "").lower()
    taluk_keywords = {
        "Tenkasi": ["tenkasi", "courtallam", "kutralam", "coutrallam", "ilanji"],
        "Shenkottai": ["shenkottai", "senkottai", "panpoli", "mekkarai"],
        "Kadayanallur": ["kadayanallur", "puliyangudi"],
        "Sankarankovil": ["sankarankovil", "sankarankoil", "thiruvengadam"],
        "Alangulam": ["alangulam"],
        "Sivagiri": ["sivagiri"],
        "Veerakeralampudur": ["veerakeralampudur", "surandai", "ayanthipuram", "sundarapandiapuram", "sundarapandiyapuram"],
    }
    for taluk, keywords in taluk_keywords.items():
        if any(keyword in text for keyword in keywords):
            return taluk
    return "Tenkasi"


def _tokenize_place_text(row: pd.Series) -> set[str]:
    text_parts = [
        row.get("place_name", ""),
        row.get("category", ""),
        row.get("types", ""),
        row.get("summary", ""),
        row.get("formatted_address", ""),
    ]
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "tenkasi",
        "tamil",
        "nadu",
        "india",
        "district",
        "place",
        "tourist",
        "attraction",
        "road",
    }
    tokens: set[str] = set()
    for part in text_parts:
        for token in str(part or "").lower().replace("|", " ").replace(",", " ").replace(".", " ").split():
            token = token.strip()
            if len(token) < 4 or token in stopwords:
                continue
            tokens.add(token)
    return tokens


def build_user_place_graph(places_df: pd.DataFrame, reviews_df: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph(name="user_place_bipartite")

    for row in places_df.itertuples(index=False):
        graph.add_node(
            f"place::{row.place_id}",
            node_type="place",
            place_id=row.place_id,
            label=row.place_name,
            category=row.category,
            rating=row.rating,
            total_user_ratings=row.total_user_ratings,
        )

    for row in reviews_df.itertuples(index=False):
        user_node = create_user_identifier(row.user_name)
        place_node = f"place::{row.place_id}"
        graph.add_node(user_node, node_type="user", label=row.user_name)
        graph.add_edge(
            user_node,
            place_node,
            relationship_type="reviewed",
            review_rating=row.rating,
            review_text=row.review_text,
        )

    return graph


def _weighted_projection(items_by_owner: dict[str, set[str]], prefix: str, relationship_type: str) -> nx.Graph:
    weights: defaultdict[tuple[str, str], int] = defaultdict(int)

    for items in items_by_owner.values():
        for left, right in combinations(sorted(items), 2):
            weights[(left, right)] += 1

    graph = nx.Graph(name=relationship_type)
    for (left, right), weight in weights.items():
        graph.add_edge(
            f"{prefix}{left}",
            f"{prefix}{right}",
            weight=weight,
            relationship_type=relationship_type,
        )

    return graph


def build_place_place_graph(places_df: pd.DataFrame, reviews_df: pd.DataFrame) -> nx.Graph:
    places_by_user: defaultdict[str, set[str]] = defaultdict(set)
    reviewer_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    place_rows = places_df.copy()
    if "formatted_address" not in place_rows.columns:
        place_rows["formatted_address"] = ""
    if "taluk" not in place_rows.columns:
        place_rows["taluk"] = place_rows["formatted_address"].map(_infer_taluk)
    if "micro_region" not in place_rows.columns:
        place_rows["micro_region"] = place_rows["taluk"]
    place_rows["rating"] = pd.to_numeric(place_rows.get("rating"), errors="coerce")
    place_rows["total_user_ratings"] = pd.to_numeric(place_rows.get("total_user_ratings"), errors="coerce")
    place_rows["keyword_tokens"] = place_rows.apply(_tokenize_place_text, axis=1)
    place_lookup = place_rows.set_index("place_id").to_dict("index")

    for row in reviews_df.itertuples(index=False):
        places_by_user[create_user_identifier(row.user_name)].add(row.place_id)

    for items in places_by_user.values():
        for left, right in combinations(sorted(items), 2):
            reviewer_counts[(left, right)] += 1

    graph = nx.Graph(name="co_reviewed_place")

    for row in place_rows.itertuples(index=False):
        graph.add_node(
            f"place::{row.place_id}",
            node_type="place",
            place_id=row.place_id,
            label=row.place_name,
            category=row.category,
            rating=row.rating,
            total_user_ratings=row.total_user_ratings,
            formatted_address=row.formatted_address,
            taluk=getattr(row, "taluk", "Tenkasi"),
            micro_region=getattr(row, "micro_region", getattr(row, "taluk", "Tenkasi")),
        )

    place_ids = list(place_lookup.keys())
    for left, right in combinations(place_ids, 2):
        pair = tuple(sorted((left, right)))
        shared_reviewers = reviewer_counts.get(pair, 0)
        left_attrs = place_lookup[left]
        right_attrs = place_lookup[right]
        same_taluk = left_attrs.get("taluk") == right_attrs.get("taluk")
        same_micro_region = left_attrs.get("micro_region") == right_attrs.get("micro_region")
        same_category = left_attrs.get("category") == right_attrs.get("category")
        left_tokens = left_attrs.get("keyword_tokens") or set()
        right_tokens = right_attrs.get("keyword_tokens") or set()
        token_union = left_tokens | right_tokens
        keyword_overlap = (len(left_tokens & right_tokens) / len(token_union)) if token_union else 0.0
        left_rating = left_attrs.get("rating")
        right_rating = right_attrs.get("rating")
        close_rating = (
            pd.notna(left_rating)
            and pd.notna(right_rating)
            and abs(float(left_rating) - float(right_rating)) <= 0.35
        )

        score = 0.0
        if shared_reviewers:
            score += min(12.0, shared_reviewers * 4.0)
        if same_taluk:
            score += 1.25
        if same_micro_region:
            score += 1.0
        if same_category and left_attrs.get("category") not in {"unknown", ""}:
            score += 1.1
        if keyword_overlap >= 0.28:
            score += min(2.0, keyword_overlap * 4.5)
        if close_rating and same_category:
            score += 0.5

        should_link = shared_reviewers > 0 or score >= 2.45
        if not should_link:
            continue

        graph.add_edge(
            f"place::{left}",
            f"place::{right}",
            weight=round(score, 3),
            relationship_type="co_reviewed_place",
            shared_reviewers=shared_reviewers,
            same_taluk=int(same_taluk),
            same_micro_region=int(same_micro_region),
            same_category=int(same_category),
            keyword_overlap=round(keyword_overlap, 3),
        )
    return graph


def build_user_user_graph(reviews_df: pd.DataFrame) -> nx.Graph:
    users_by_place: defaultdict[str, set[str]] = defaultdict(set)

    for row in reviews_df.itertuples(index=False):
        users_by_place[row.place_id].add(create_user_identifier(row.user_name))

    graph = _weighted_projection(users_by_place, "", "co_reviewed_user")
    for node in list(graph.nodes):
        graph.nodes[node].update({"node_type": "user", "label": node.replace("user::", "").replace("_", " ").title()})
    return graph


def build_edges_dataframe(user_place_graph: nx.Graph, place_graph: nx.Graph, user_graph: nx.Graph) -> pd.DataFrame:
    edge_rows: list[dict[str, str | int | float]] = []

    for graph in (user_place_graph, place_graph, user_graph):
        for left, right, attrs in graph.edges(data=True):
            edge_rows.append(
                {
                    "node1": left,
                    "node2": right,
                    "relationship_type": attrs.get("relationship_type", graph.name),
                    "weight": attrs.get("weight", 1),
                }
            )

    return pd.DataFrame(edge_rows)


def graph_to_nodes_dataframe(graph: nx.Graph, graph_name: str) -> pd.DataFrame:
    rows: list[dict[str, str | int | float]] = []
    for node, attrs in graph.nodes(data=True):
        row = {"node": node, "graph_name": graph_name}
        row.update(attrs)
        rows.append(row)
    return pd.DataFrame(rows)
