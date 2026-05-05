from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from .config import COMMUNITIES_DIR, OUTPUTS_DIR, PLOTS_DIR, ProjectConfig, REFERENCE_DIR


TALUK_PROFILES = {
    "Tenkasi": {
        "keywords": ["tenkasi", "courtallam", "kutralam", "coutrallam", "ilanji"],
        "description": "Core tourism belt anchored by waterfalls, temples, and the urban visitor gateway.",
        "color": "#ef476f",
    },
    "Shenkottai": {
        "keywords": ["shenkottai", "senkottai", "panpoli", "mekkarai"],
        "description": "Western Ghats approach zone with hill temples, scenic roads, and border-linked spots.",
        "color": "#06d6a0",
    },
    "Kadayanallur": {
        "keywords": ["kadayanallur", "puliyangudi"],
        "description": "Northern taluk cluster with local heritage, viewpoints, and smaller religious destinations.",
        "color": "#118ab2",
    },
    "Sankarankovil": {
        "keywords": ["sankarankovil", "sankarankoil", "thiruvengadam"],
        "description": "Pilgrimage-focused zone with strong temple-centric tourism movement.",
        "color": "#ffd166",
    },
    "Alangulam": {
        "keywords": ["alangulam"],
        "description": "Dispersed destination belt with semi-rural cultural and scenic travel stops.",
        "color": "#8ecae6",
    },
    "Sivagiri": {
        "keywords": ["sivagiri"],
        "description": "Smaller niche pocket with locally important destinations and low-noise travel patterns.",
        "color": "#9b5de5",
    },
    "Veerakeralampudur": {
        "keywords": ["veerakeralampudur", "surandai", "sundarapandiapuram", "sundarapandiyapuram"],
        "description": "Mixed scenic and town-edge tourism corridor with underexplored local attractions.",
        "color": "#f4a261",
    },
    "Thiruvengadam": {
        "keywords": ["thiruvengadam"],
        "description": "Peripheral taluk with pilgrimage links and lower-volume tourism nodes.",
        "color": "#52b788",
    },
}

MICRO_REGIONS = {
    "Courtallam Falls Circuit": ["courtallam", "kutralam", "coutrallam", "five falls", "main falls", "old courtallam", "chitraruvi"],
    "Temple Heritage Belt": ["temple", "kovil", "kasi viswanathar", "thirumalai", "sabha", "dargah", "church", "mosque"],
    "Dam and Reservoir Belt": ["dam", "reservoir", "park", "gundar", "gadananathi", "ramanathi", "karuppanathi", "adavinainar"],
    "Western Ghats Scenic Belt": ["mekkarai", "panpoli", "palaruvi", "viewpoint", "ghat", "hill", "trek"],
    "Town and Cultural Core": ["tenkasi", "bus stand", "market", "junction"],
}

CATEGORY_LABELS = {
    "tourist_attraction": "Tourist Attraction",
    "hindu_temple": "Temple",
    "church": "Church",
    "mosque": "Mosque",
    "park": "Park",
    "museum": "Museum",
    "natural_feature": "Nature Spot",
    "point_of_interest": "Point of Interest",
}

INTEREST_RULES = {
    "Temple": ["temple", "kovil", "hindu_temple"],
    "Waterfalls": ["falls", "waterfall", "aruvi"],
    "Dam": ["dam", "reservoir"],
    "Park/Garden": ["park", "garden"],
    "Wildlife Sanctuary": ["sanctuary", "wildlife", "forest"],
    "Viewpoint/Hills": ["viewpoint", "hill", "ghat", "mekkarai", "panpoli"],
    "Museum": ["museum"],
    "Memorial": ["memorial"],
    "Tourist Attraction": ["tourist_attraction", "tourist attraction"],
}


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _load_json(path: Path):
    return json.loads(path.read_text()) if path.exists() else {}


def _load_json_list(path: Path) -> list[dict]:
    return json.loads(path.read_text()) if path.exists() else []


def _display_label(node: str, place_lookup: dict[str, str]) -> str:
    if node.startswith("place::"):
        return place_lookup.get(node.replace("place::", "", 1), node)
    if node.startswith("user::"):
        return node.replace("user::", "").replace("_", " ").title()
    return node


def _load_places_dataset(config: ProjectConfig) -> pd.DataFrame:
    places_df = _load_csv(config.places_csv)
    if not places_df.empty:
        return places_df

    legacy_path = REFERENCE_DIR / "legacy" / "tenkasi_clean.csv"
    legacy_df = _load_csv(legacy_path)
    if legacy_df.empty:
        return legacy_df

    legacy_df = legacy_df.rename(columns={"name": "place_name"})
    legacy_df["place_id"] = legacy_df.index.map(lambda idx: f"legacy_place_{idx + 1}")
    legacy_df["rating"] = pd.NA
    legacy_df["total_user_ratings"] = pd.NA
    legacy_df["formatted_address"] = "Tenkasi, Tamil Nadu"
    legacy_df["google_maps_url"] = pd.NA
    legacy_df["photo_name"] = pd.NA
    legacy_df["photo_count"] = 0
    legacy_df["summary"] = pd.NA
    return legacy_df[
        [
            "place_id",
            "place_name",
            "category",
            "rating",
            "total_user_ratings",
            "formatted_address",
            "google_maps_url",
            "summary",
            "photo_name",
            "photo_count",
        ]
    ]


def _load_reviews_dataset(config: ProjectConfig) -> pd.DataFrame:
    reviews_df = _load_csv(config.reviews_csv)
    if not reviews_df.empty:
        return reviews_df
    return pd.DataFrame(columns=["user_name", "place_id", "place_name", "rating", "review_text"])


def _to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _assign_taluk(value: str) -> str:
    text = str(value or "").lower()
    for taluk, profile in TALUK_PROFILES.items():
        if any(keyword in text for keyword in profile["keywords"]):
            return taluk
    return "Tenkasi"


def _assign_micro_region(value: str) -> str:
    text = str(value or "").lower()
    for region, keywords in MICRO_REGIONS.items():
        if any(keyword in text for keyword in keywords):
            return region
    return "General Tenkasi Circuit"


def _category_display(value: str) -> str:
    key = str(value or "unknown").strip()
    return CATEGORY_LABELS.get(key, key.replace("_", " ").title())


def _build_photo_url(photo_name: str | float | None, api_key: str) -> str | None:
    if not api_key:
        return None
    if pd.isna(photo_name) or not str(photo_name).strip():
        return None
    return f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=540&key={api_key}"


def _network_role(row: pd.Series) -> str:
    if row.get("betweenness_centrality", 0) >= 0.05:
        return "Bridge Place"
    if row.get("pagerank", 0) >= 0.03:
        return "Influential Hub"
    if row.get("closeness_centrality", 0) >= 0.16:
        return "Fast-Reach Node"
    if row.get("rating", 0) >= 4.5 and row.get("total_user_ratings", 0) < 300:
        return "Hidden Gem"
    return "Network Participant"


def _is_recommendable_place(row: pd.Series) -> bool:
    text = " ".join(
        [
            str(row.get("place_name", "")),
            str(row.get("formatted_address", "")),
            str(row.get("category", "")),
            str(row.get("summary", "")),
        ]
    ).lower()
    blocked_tokens = ["bengaluru", "varkala", "defence colony", "travel agency", "transportation_service"]
    if any(token in text for token in blocked_tokens):
        return False
    if row.get("category") in {"travel_agency", "transportation_service", "local_government_office"}:
        return False
    return True


def _derive_interests(row: pd.Series) -> list[str]:
    text = " ".join(
        [
            str(row.get("place_name", "")),
            str(row.get("category", "")),
            str(row.get("category_label", "")),
            str(row.get("types", "")),
            str(row.get("summary", "")),
            str(row.get("micro_region", "")),
        ]
    ).lower()
    matches = [interest for interest, keywords in INTEREST_RULES.items() if any(keyword in text for keyword in keywords)]
    if not matches:
        matches = ["Tourist Attraction"]
    return matches[:4]


def _estimate_remote_score(row: pd.Series) -> int:
    text = " ".join([str(row.get("place_name", "")), str(row.get("formatted_address", "")), str(row.get("micro_region", ""))]).lower()
    score = 15
    if any(token in text for token in ["mekkarai", "palaruvi", "achankovil", "ghat", "hill", "forest", "sanctuary"]):
        score += 35
    if any(token in text for token in ["courtallam", "kutralam", "dam", "reservoir", "viewpoint"]):
        score += 20
    if row.get("connection_count", 0) >= 25:
        score -= 10
    if row.get("taluk") == "Tenkasi":
        score -= 8
    return max(5, min(80, score))


def _derive_theme(row: pd.Series) -> str:
    category = str(row.get("category", "unknown"))
    region = str(row.get("micro_region", ""))
    if "Falls" in region or category in {"natural_feature", "park"}:
        return "Nature"
    if category in {"hindu_temple", "church", "mosque"} or "Temple" in row.get("category_label", ""):
        return "Spiritual"
    if "Dam" in region or "Reservoir" in region:
        return "Scenic Drive"
    if row.get("betweenness_centrality", 0) >= 0.04:
        return "Connector"
    return "Explore"


def _prepare_places(places_df: pd.DataFrame, place_metrics_df: pd.DataFrame, api_key: str) -> pd.DataFrame:
    if places_df.empty:
        return places_df

    places = places_df.copy()
    places = _to_numeric(
        places,
        [
            "rating",
            "total_user_ratings",
            "photo_count",
        ],
    )
    for column in ["formatted_address", "summary", "google_maps_url", "types", "photo_name"]:
        if column not in places.columns:
            places[column] = ""
        places[column] = places[column].fillna("")

    existing_taluk = places["taluk"].fillna("") if "taluk" in places.columns else pd.Series([""] * len(places))
    places["taluk"] = existing_taluk.mask(existing_taluk.eq(""), places["formatted_address"].map(_assign_taluk))

    existing_micro = places["micro_region"].fillna("") if "micro_region" in places.columns else pd.Series([""] * len(places))
    places["micro_region"] = existing_micro.mask(
        existing_micro.eq(""),
        (places["place_name"] + " " + places["formatted_address"] + " " + places["summary"]).map(_assign_micro_region),
    )

    places["category"] = places.get("category", "unknown").fillna("unknown")
    places["category_label"] = places["category"].map(_category_display)

    if not place_metrics_df.empty:
        metrics = place_metrics_df.copy()
        metrics["place_id"] = metrics["node"].str.replace("place::", "", regex=False)
        places = places.merge(
            metrics[
                [
                    "place_id",
                    "degree_centrality",
                    "betweenness_centrality",
                    "closeness_centrality",
                    "eigenvector_centrality",
                    "katz_centrality",
                    "pagerank",
                    "hits_hub",
                    "hits_authority",
                    "average_rank",
                ]
            ],
            on="place_id",
            how="left",
        )
    else:
        for col in [
            "degree_centrality",
            "betweenness_centrality",
            "closeness_centrality",
            "eigenvector_centrality",
            "katz_centrality",
            "pagerank",
            "hits_hub",
            "hits_authority",
            "average_rank",
        ]:
            places[col] = 0.0

    metric_cols = [
        "degree_centrality",
        "betweenness_centrality",
        "closeness_centrality",
        "eigenvector_centrality",
        "katz_centrality",
        "pagerank",
        "hits_hub",
        "hits_authority",
        "average_rank",
    ]
    places = _to_numeric(places, metric_cols)
    places["summary"] = places["summary"].mask(places["summary"].eq(""), "Live Google Places profile available for this destination.")
    places["photo_url"] = places["photo_name"].map(lambda name: _build_photo_url(name, api_key))
    places["theme"] = places.apply(_derive_theme, axis=1)
    places["network_role"] = places.apply(_network_role, axis=1)
    places["featured_score"] = (
        places["rating"].fillna(0) * 16
        + places["total_user_ratings"].fillna(0) * 0.06
        + places["pagerank"].fillna(0) * 180
        + places["betweenness_centrality"].fillna(0) * 120
    )
    places["recommendation_score"] = (
        places["rating"].fillna(0) * 15
        + places["closeness_centrality"].fillna(0) * 120
        + places["pagerank"].fillna(0) * 140
        + places["betweenness_centrality"].fillna(0) * 90
        + places["photo_count"].fillna(0) * 0.08
    )
    places["facility_tags"] = places["types"].map(
        lambda value: [
            token.replace("_", " ").title()
            for token in str(value or "").split("|")
            if token and token not in {"point_of_interest", "establishment"}
        ][:4]
    )
    places["interest_tags"] = places.apply(_derive_interests, axis=1)
    return places


def _build_category_summary(places_df: pd.DataFrame) -> list[dict]:
    if places_df.empty:
        return []
    summary = (
        places_df.groupby("category_label")
        .agg(count=("place_id", "count"), avg_rating=("rating", "mean"))
        .reset_index()
        .sort_values(by="count", ascending=False)
    )
    summary["avg_rating"] = summary["avg_rating"].fillna(0).round(2)
    summary = summary.rename(columns={"category_label": "category"})
    return summary.to_dict(orient="records")


def _build_taluk_summary(places_df: pd.DataFrame) -> list[dict]:
    if places_df.empty:
        return []
    summary = (
        places_df.groupby("taluk")
        .agg(
            count=("place_id", "count"),
            avg_rating=("rating", "mean"),
            avg_pagerank=("pagerank", "mean"),
        )
        .reset_index()
        .sort_values(by="count", ascending=False)
    )
    summary["avg_rating"] = summary["avg_rating"].fillna(0).round(2)
    summary["avg_pagerank"] = summary["avg_pagerank"].fillna(0).round(4)
    summary["description"] = summary["taluk"].map(
        lambda taluk: TALUK_PROFILES.get(taluk, {}).get("description", "Tenkasi tourism cluster")
    )
    summary["color"] = summary["taluk"].map(lambda taluk: TALUK_PROFILES.get(taluk, {}).get("color", "#5f92ff"))
    return summary.to_dict(orient="records")


def _metric_top(metrics_df: pd.DataFrame, metric: str, limit: int = 10) -> list[dict]:
    if metrics_df.empty or metric not in metrics_df.columns:
        return []
    return metrics_df.nlargest(limit, metric).to_dict(orient="records")


def _build_hidden_gems(places_df: pd.DataFrame) -> list[dict]:
    if places_df.empty:
        return []
    gems = places_df.copy()
    gems = gems[
        (gems["rating"].fillna(0) >= 4.1)
        & (gems["total_user_ratings"].fillna(0) >= 8)
        & (gems["total_user_ratings"].fillna(0) <= 450)
    ]
    gems["hidden_gem_score"] = (
        gems["rating"].fillna(0) * 12
        + gems["betweenness_centrality"].fillna(0) * 140
        + gems["closeness_centrality"].fillna(0) * 50
        - gems["total_user_ratings"].fillna(0) * 0.025
    )
    gems = gems.sort_values(by="hidden_gem_score", ascending=False)
    return gems.head(18).to_dict(orient="records")


def _build_place_lookup(places_df: pd.DataFrame) -> dict[str, str]:
    return places_df.set_index("place_id")["place_name"].to_dict() if not places_df.empty else {}


def _load_graph_payload(path: Path) -> dict:
    if not path.exists():
        return {"nodes": [], "links": []}
    payload = _load_json(path)
    if "links" not in payload and "edges" in payload:
        payload["links"] = payload["edges"]
    return payload


def _normalize_graph_payload(graph_payload: dict, places_df: pd.DataFrame, communities: dict) -> dict:
    place_lookup = _build_place_lookup(places_df)
    place_index = places_df.set_index("place_id").to_dict("index") if not places_df.empty else {}
    community_map: dict[str, int] = {}
    for idx, group in enumerate(communities.get("louvain", []), start=1):
        for label in group:
            community_map[label] = idx

    nodes = []
    for node in graph_payload.get("nodes", []):
        node_id = node.get("id") or node.get("node") or node.get("name")
        if not str(node_id).startswith("place::"):
            continue
        place_id = str(node_id).replace("place::", "", 1)
        place_attrs = place_index.get(place_id, {})
        label = node.get("label") or _display_label(node_id, place_lookup)
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "place_id": place_id,
                "category": place_attrs.get("category_label", node.get("category", "unknown")),
                "taluk": place_attrs.get("taluk", _assign_taluk(label)),
                "pagerank": float(node.get("pagerank", place_attrs.get("pagerank", 0)) or 0),
                "degree": float(node.get("degree_centrality", place_attrs.get("degree_centrality", 0)) or 0),
                "community": community_map.get(label, 0),
                "node_type": node.get("node_type", "place"),
                "photo_url": place_attrs.get("photo_url"),
                "network_role": place_attrs.get("network_role", "Network Participant"),
            }
        )

    links = []
    for link in graph_payload.get("links", []):
        source = link.get("source")
        target = link.get("target")
        if isinstance(source, dict):
            source = source.get("id")
        if isinstance(target, dict):
            target = target.get("id")
        if not str(source).startswith("place::") or not str(target).startswith("place::"):
            continue
        links.append(
            {
                "source": source,
                "target": target,
                "weight": float(link.get("weight", 1) or 1),
            }
        )
    return {"nodes": nodes, "links": links}


def _augment_connections(places_df: pd.DataFrame, graph_data: dict) -> pd.DataFrame:
    if places_df.empty:
        return places_df
    counts: Counter[str] = Counter()
    for link in graph_data.get("links", []):
        counts[str(link["source"]).replace("place::", "", 1)] += 1
        counts[str(link["target"]).replace("place::", "", 1)] += 1
    enriched = places_df.copy()
    enriched["connection_count"] = enriched["place_id"].map(lambda pid: counts.get(pid, 0))
    return enriched


def _build_graph_companions(graph_data: dict, place_lookup: dict[str, str]) -> dict[str, list[dict]]:
    companions: defaultdict[str, list[dict]] = defaultdict(list)
    for link in graph_data.get("links", []):
        source_id = str(link["source"]).replace("place::", "", 1)
        target_id = str(link["target"]).replace("place::", "", 1)
        weight = float(link.get("weight", 1) or 1)
        companions[source_id].append({"place_id": target_id, "label": place_lookup.get(target_id, target_id), "weight": weight})
        companions[target_id].append({"place_id": source_id, "label": place_lookup.get(source_id, source_id), "weight": weight})
    for place_id, rows in companions.items():
        companions[place_id] = sorted(rows, key=lambda item: item["weight"], reverse=True)[:5]
    return dict(companions)


def _build_recommendation_catalog(places_df: pd.DataFrame, companions: dict[str, list[dict]]) -> list[dict]:
    if places_df.empty:
        return []
    rows = places_df.copy()
    rows = rows[rows.apply(_is_recommendable_place, axis=1)]
    rows["remote_score"] = rows.apply(_estimate_remote_score, axis=1)
    rows = rows.sort_values(
        by=["recommendation_score", "featured_score", "rating"],
        ascending=False,
    )
    output = []
    for row in rows.itertuples(index=False):
        reasons = [
            row.network_role,
            f"{int(getattr(row, 'connection_count', 0))} network links",
            f"{row.category_label} hotspot",
        ]
        output.append(
            {
                **row._asdict(),
                "reasons": reasons,
                "companions": companions.get(row.place_id, []),
            }
        )
    return output


def _build_itineraries(places_df: pd.DataFrame) -> dict[str, list[dict]]:
    if places_df.empty:
        return {}
    places_df = places_df[places_df.apply(_is_recommendable_place, axis=1)].copy()
    if places_df.empty:
        return {}

    theme_order = ["Nature", "Spiritual", "Scenic Drive", "Connector", "Explore"]
    themed = {theme: subset.sort_values(by="recommendation_score", ascending=False) for theme, subset in places_df.groupby("theme")}

    itineraries: dict[str, list[dict]] = {}
    for duration, size in [("1 Day", 4), ("2 Days", 8), ("3 Days", 12)]:
        picks: list[dict] = []
        used_ids: set[str] = set()
        for theme in theme_order:
            for row in themed.get(theme, pd.DataFrame()).itertuples(index=False):
                if row.place_id in used_ids:
                    continue
                picks.append(row._asdict())
                used_ids.add(row.place_id)
                if len(picks) >= size:
                    break
            if len(picks) >= size:
                break
        if len(picks) < size:
            fallback = places_df.sort_values(by="recommendation_score", ascending=False)
            for row in fallback.itertuples(index=False):
                if row.place_id in used_ids:
                    continue
                picks.append(row._asdict())
                used_ids.add(row.place_id)
                if len(picks) >= size:
                    break
        itineraries[duration] = picks
    return itineraries


def _build_smart_circuits(places_df: pd.DataFrame) -> list[dict]:
    if places_df.empty:
        return []
    places_df = places_df[places_df.apply(_is_recommendable_place, axis=1)].copy()
    if places_df.empty:
        return []
    circuits = []
    for theme, subset in places_df.groupby("theme"):
        top = subset.sort_values(by="recommendation_score", ascending=False).head(5)
        circuits.append(
            {
                "title": theme,
                "description": f"{theme} circuit curated from rating, connectivity, and regional clustering signals.",
                "places": top.to_dict(orient="records"),
            }
        )
    return sorted(circuits, key=lambda item: len(item["places"]), reverse=True)[:5]


def _build_predicted_pairs(predictions_df: pd.DataFrame, place_lookup: dict[str, str]) -> list[dict]:
    if predictions_df.empty:
        return []
    scored = predictions_df.copy()
    for column in ["common_neighbors", "jaccard_coefficient", "adamic_adar_index"]:
        if column not in scored.columns:
            scored[column] = 0
    scored["pair_score"] = (
        scored["common_neighbors"].fillna(0) * 2
        + scored["jaccard_coefficient"].fillna(0) * 20
        + scored["adamic_adar_index"].fillna(0)
    )
    scored["node1_label"] = scored["node1"].map(lambda value: _display_label(value, place_lookup))
    scored["node2_label"] = scored["node2"].map(lambda value: _display_label(value, place_lookup))
    return scored.sort_values(by="pair_score", ascending=False).head(12).to_dict(orient="records")


def _build_community_highlights(place_communities: dict[str, list[list[str]]], places_df: pd.DataFrame) -> list[dict]:
    if places_df.empty:
        return []
    label_to_row = {row.place_name: row for row in places_df.itertuples(index=False)}
    highlights = []
    for idx, group in enumerate(place_communities.get("louvain", []), start=1):
        rows = [label_to_row[label] for label in group if label in label_to_row]
        if not rows:
            continue
        category_mix = Counter(getattr(row, "category_label", "Unknown") for row in rows).most_common(3)
        taluk_mix = Counter(getattr(row, "taluk", "Tenkasi") for row in rows).most_common(2)
        highlights.append(
            {
                "id": idx,
                "size": len(rows),
                "top_categories": [item[0] for item in category_mix],
                "top_taluks": [item[0] for item in taluk_mix],
                "places": [row.place_name for row in rows[:8]],
            }
        )
    return highlights


def load_dashboard_data() -> dict:
    config = ProjectConfig()
    places_raw = _load_places_dataset(config)
    reviews_df = _load_reviews_dataset(config)
    edges_df = _load_csv(config.edges_csv)
    place_metrics_df = _load_csv(OUTPUTS_DIR / "metrics" / "place_network_metrics.csv")
    user_metrics_df = _load_csv(OUTPUTS_DIR / "metrics" / "user_network_metrics.csv")
    place_stats = _load_json(OUTPUTS_DIR / "metrics" / "place_network_stats.json")
    user_stats = _load_json(OUTPUTS_DIR / "metrics" / "user_network_stats.json")
    place_communities = _load_json(COMMUNITIES_DIR / "place_network_communities.json")
    predictions_df = _load_csv(OUTPUTS_DIR / "link_prediction" / "place_network_predictions.csv")
    insights = _load_json(OUTPUTS_DIR / "insights.json")
    graph_payload = _load_graph_payload(OUTPUTS_DIR / "graphs" / "place_network.json")
    research_notes = _load_json_list(REFERENCE_DIR / "tenkasi_research_notes.json")

    places_df = _prepare_places(places_raw, place_metrics_df, config.api_key)
    place_lookup = _build_place_lookup(places_df)

    for key in ("girvan_newman", "louvain"):
        groups = place_communities.get(key, [])
        place_communities[key] = [[_display_label(node, place_lookup) for node in group] for group in groups]

    graph_data = _normalize_graph_payload(graph_payload, places_df, place_communities)
    places_df = _augment_connections(places_df, graph_data)
    place_lookup = _build_place_lookup(places_df)
    companions = _build_graph_companions(graph_data, place_lookup)

    category_summary = _build_category_summary(places_df)
    taluk_summary = _build_taluk_summary(places_df)
    hidden_gems = _build_hidden_gems(places_df)
    featured_places = places_df.sort_values(by="featured_score", ascending=False).head(15).to_dict(orient="records") if not places_df.empty else []
    most_visited_place = (
        places_df.sort_values(by=["total_user_ratings", "rating"], ascending=False).head(1).to_dict(orient="records")[0]
        if not places_df.empty
        else {}
    )
    bridge_places = _metric_top(place_metrics_df, "betweenness_centrality", 12)
    centrality_views = {
        "degree": _metric_top(place_metrics_df, "degree_centrality", 15),
        "closeness": _metric_top(place_metrics_df, "closeness_centrality", 15),
        "betweenness": _metric_top(place_metrics_df, "betweenness_centrality", 15),
        "pagerank": _metric_top(place_metrics_df, "pagerank", 15),
        "eigenvector": _metric_top(place_metrics_df, "eigenvector_centrality", 15),
        "katz": _metric_top(place_metrics_df, "katz_centrality", 15),
        "hub": _metric_top(place_metrics_df, "hits_hub", 15),
        "authority": _metric_top(place_metrics_df, "hits_authority", 15),
    }
    analytics_available = not place_metrics_df.empty
    reviews_available = not reviews_df.empty

    plot_catalog = {
        "category_distribution": PLOTS_DIR / "place_categories.png",
        "degree_distribution": PLOTS_DIR / "place_network_degree_distribution.png",
        "pagerank_leaders": PLOTS_DIR / "place_network_centrality.png",
        "betweenness_leaders": PLOTS_DIR / "place_network_betweenness.png",
        "closeness_leaders": PLOTS_DIR / "place_network_closeness.png",
        "community_sizes": PLOTS_DIR / "place_network_community_sizes.png",
        "rating_vs_pagerank": PLOTS_DIR / "place_network_rating_vs_pagerank.png",
        "rating_vs_betweenness": PLOTS_DIR / "place_network_rating_vs_betweenness.png",
        "network_plot": PLOTS_DIR / "place_network_graph.png",
    }

    community_highlights = _build_community_highlights(place_communities, places_df)
    top_predictions = _build_predicted_pairs(predictions_df, place_lookup)
    recommendation_places = _build_recommendation_catalog(places_df, companions)
    smart_circuits = _build_smart_circuits(places_df)

    homepage_metrics = [
        {"label": "Tourism Nodes", "value": len(places_df), "subtext": "validated Google Places destinations"},
        {"label": "Place Edges", "value": int(place_stats.get("edges", 0) or 0), "subtext": "weighted similarity and co-review links"},
        {"label": "Reviews", "value": len(reviews_df), "subtext": "user interactions powering the graph"},
        {"label": "Communities", "value": len(place_communities.get("louvain", [])), "subtext": "detected tourism clusters"},
    ]

    return {
        "location_name": "Tenkasi",
        "places": places_df.to_dict(orient="records"),
        "reviews": reviews_df.to_dict(orient="records"),
        "edges_count": int(len(edges_df)),
        "place_rankings": place_metrics_df.to_dict(orient="records"),
        "user_rankings": user_metrics_df.to_dict(orient="records"),
        "place_stats": place_stats,
        "user_stats": user_stats,
        "place_communities": place_communities,
        "community_highlights": community_highlights,
        "predictions": predictions_df.to_dict(orient="records"),
        "top_predictions": top_predictions,
        "insights": insights,
        "most_visited_place": most_visited_place,
        "category_summary": category_summary,
        "taluk_summary": taluk_summary,
        "featured_places": featured_places,
        "hidden_gems": hidden_gems,
        "bridge_places": bridge_places,
        "centrality_views": centrality_views,
        "homepage_metrics": homepage_metrics,
        "graph_data": graph_data,
        "plot_catalog": plot_catalog,
        "graph_files": {
            "place_gexf": OUTPUTS_DIR / "graphs" / "place_network.gexf",
            "place_json": OUTPUTS_DIR / "graphs" / "place_network.json",
        },
        "exports": {
            "place_nodes": OUTPUTS_DIR / "exports" / "place_network_nodes.csv",
            "place_edges": OUTPUTS_DIR / "exports" / "place_network_edges.csv",
            "neo4j_places": OUTPUTS_DIR / "neo4j" / "place_nodes.csv",
            "neo4j_users": OUTPUTS_DIR / "neo4j" / "user_nodes.csv",
            "neo4j_reviews": OUTPUTS_DIR / "neo4j" / "reviewed_edges.csv",
            "neo4j_place_edges": OUTPUTS_DIR / "neo4j" / "place_edges.csv",
            "neo4j_user_edges": OUTPUTS_DIR / "neo4j" / "user_edges.csv",
            "neo4j_cypher": OUTPUTS_DIR / "neo4j" / "import.cypher",
        },
        "recommendation_places": recommendation_places,
        "itineraries": _build_itineraries(places_df),
        "smart_circuits": smart_circuits,
        "reviews_available": reviews_available,
        "analytics_available": analytics_available,
        "places_have_ratings": places_df["rating"].notna().any() if not places_df.empty else False,
        "research_notes": research_notes,
        "companions": companions,
    }
