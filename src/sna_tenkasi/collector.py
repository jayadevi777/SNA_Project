from __future__ import annotations

import argparse
import json
import math
import time
from typing import Any

import pandas as pd
import requests

from .config import ProjectConfig, ensure_directories


TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places"

ALLOWED_LOCATION_TOKENS = {
    "tenkasi",
    "courtallam",
    "kutralam",
    "coutrallam",
    "shenkottai",
    "senkottai",
    "panpoli",
    "ilanji",
    "mekkarai",
    "sundarapandiapuram",
    "pottalpudur",
    "sankarankovil",
    "kadayanallur",
    "surandai",
    "alangulam",
    "sivagiri",
    "puliyangudi",
    "veerakeralampudur",
    "achankovil",
    "thiruvengadam",
    "surandai",
    "achanputhur",
    "ayikudi",
    "sundarapandiyapuram",
    "gundar",
    "ramanathi",
    "karuppanathi",
    "gadananathi",
    "adavinainar",
    "manalar",
}


class GooglePlacesCollector:
    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        if not self.config.api_key:
            raise ValueError(
                "GOOGLE_PLACES_API_KEY is missing. Add it to your environment or .env file."
            )

    def fetch_places(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        raw_pages: list[dict[str, Any]] = []
        unique_places: dict[str, dict[str, Any]] = {}
        generic_queries = list(dict.fromkeys(self.config.text_queries))
        seed_queries = [f"{seed} Tenkasi" for seed in self.config.seed_places]
        all_queries = generic_queries + seed_queries
        candidate_limit = max(self.config.target_place_count + 25, int(self.config.target_place_count * 1.35))

        for query in all_queries:
            next_page_token: str | None = None
            for _page_idx in range(self.config.pages_per_query):
                payload = self._text_search(query, next_page_token)
                raw_pages.append({"query": query, "payload": payload})

                for result in payload.get("places", []):
                    place_id = result.get("id")
                    if not place_id:
                        continue
                    enriched = dict(result)
                    enriched.setdefault("_discovery_queries", []).append(query)
                    if place_id in unique_places:
                        unique_places[place_id]["_discovery_queries"].append(query)
                    else:
                        unique_places[place_id] = enriched

                next_page_token = payload.get("nextPageToken")
                if not next_page_token or len(unique_places) >= candidate_limit:
                    break
                time.sleep(2)
            if len(unique_places) >= candidate_limit:
                break

        ranked_results = sorted(
            unique_places.values(),
            key=lambda item: self._score_place_result(item),
            reverse=True,
        )
        shortlisted = [
            result for result in ranked_results if self._is_relevant_place(result)
        ][: self.config.target_place_count]
        return raw_pages, shortlisted

    def _text_search(self, query: str, page_token: str | None = None) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.config.api_key,
            "X-Goog-FieldMask": ",".join(
                [
                    "places.id",
                    "places.displayName",
                    "places.formattedAddress",
                    "places.types",
                    "places.rating",
                    "places.userRatingCount",
                    "places.photos",
                    "nextPageToken",
                ]
            ),
        }
        body: dict[str, Any] = {
            "textQuery": query,
            "pageSize": 20,
            "languageCode": "en",
            "regionCode": "IN",
        }
        if page_token:
            body["pageToken"] = page_token
        response = requests.post(TEXT_SEARCH_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        return response.json()

    def _is_relevant_place(self, result: dict[str, Any]) -> bool:
        query_text = " ".join(result.get("_discovery_queries", [])).lower()
        display_name = result.get("displayName", {})
        if isinstance(display_name, dict):
            name = (display_name.get("text") or "").lower()
        else:
            name = str(display_name or "").lower()
        address = (result.get("formattedAddress") or "").lower()
        types = set(result.get("types", []))
        tourism_bias_types = {
            "tourist_attraction",
            "hindu_temple",
            "mosque",
            "church",
            "park",
            "museum",
            "campground",
            "rv_park",
            "natural_feature",
        }
        noisy_types = {
            "school",
            "hospital",
            "pharmacy",
            "lodging",
            "restaurant",
            "store",
            "gas_station",
            "bank",
            "bus_station",
        }
        exact_seed = any(seed.lower() in f"{name} {address}" for seed in self.config.seed_places)
        local_context = f"{name} {address} {query_text}"
        in_scope_location = any(token in local_context for token in ALLOWED_LOCATION_TOKENS)

        if exact_seed:
            return True
        if not in_scope_location:
            return False
        if types & tourism_bias_types:
            return True
        if types & noisy_types and not ("falls" in name or "dam" in name or "temple" in name or "dargah" in name):
            return False
        return in_scope_location

    def _score_place_result(self, result: dict[str, Any]) -> float:
        types = set(result.get("types", []))
        display_name = result.get("displayName", {})
        if isinstance(display_name, dict):
            name = (display_name.get("text") or "").lower()
        else:
            name = str(display_name or "").lower()
        address = (result.get("formattedAddress") or "").lower()
        ratings_total = float(result.get("userRatingCount") or 0)
        rating = float(result.get("rating") or 0)
        discovery_queries = " ".join(result.get("_discovery_queries", [])).lower()

        score = 0.0
        score += rating * 8
        score += math.log1p(ratings_total) * 12
        score += min(len(set(result.get("_discovery_queries", []))), 6) * 3

        high_value_types = {
            "tourist_attraction",
            "natural_feature",
            "park",
            "museum",
            "hindu_temple",
            "mosque",
            "church",
        }
        low_value_types = {
            "lodging",
            "school",
            "hospital",
            "pharmacy",
            "bus_station",
            "bank",
        }
        if types & high_value_types:
            score += 14
        if types & low_value_types:
            score -= 10

        if any(token in name for token in ("falls", "fall", "aruvi", "dam", "temple", "dargah", "sabha", "park")):
            score += 10
        if any(seed.lower() in f"{name} {address}" for seed in self.config.seed_places):
            score += 24
        if any(token in discovery_queries for token in ("hidden", "eco", "viewpoint", "trekking", "dam", "heritage")):
            score += 4

        return score

    def fetch_place_details(self, place_ids: list[str]) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        for place_id in place_ids:
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.config.api_key,
                "X-Goog-FieldMask": ",".join(
                    [
                        "id",
                        "displayName",
                        "rating",
                        "userRatingCount",
                        "types",
                        "reviews",
                        "googleMapsUri",
                        "formattedAddress",
                        "editorialSummary",
                        "photos",
                    ]
                ),
            }
            response = requests.get(f"{PLACE_DETAILS_URL}/{place_id}", headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            details.append(payload)
            time.sleep(0.2)

        return details


def _normalize_places(
    detail_payloads: list[dict[str, Any]], max_reviews_per_place: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    place_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []

    for payload in detail_payloads:
        result = payload
        if not result:
            continue

        types = result.get("types", [])
        category = types[0] if types else "unknown"
        editorial = result.get("editorialSummary", {})
        display_name = result.get("displayName", {})
        place_name = display_name.get("text") if isinstance(display_name, dict) else display_name
        photos = result.get("photos", [])
        first_photo = photos[0] if photos else {}
        place_rows.append(
            {
                "place_id": result.get("id"),
                "place_name": place_name,
                "category": category,
                "rating": result.get("rating"),
                "total_user_ratings": result.get("userRatingCount"),
                "types": "|".join(types),
                "formatted_address": result.get("formattedAddress"),
                "google_maps_url": result.get("googleMapsUri"),
                "summary": editorial.get("text") if isinstance(editorial, dict) else editorial,
                "photo_name": first_photo.get("name"),
                "photo_count": len(photos),
            }
        )

        for review in result.get("reviews", [])[:max_reviews_per_place]:
            author = review.get("authorAttribution", {}) if isinstance(review.get("authorAttribution"), dict) else {}
            review_rows.append(
                {
                    "user_name": author.get("displayName", "Anonymous"),
                    "place_id": result.get("id"),
                    "place_name": place_name,
                    "rating": review.get("rating"),
                    "review_text": (review.get("text") or {}).get("text", "") if isinstance(review.get("text"), dict) else review.get("text", ""),
                    "review_time": review.get("relativePublishTimeDescription"),
                }
            )

    places_df = pd.DataFrame(place_rows)
    if places_df.empty:
        places_df = pd.DataFrame(
            columns=[
                "place_id",
                "place_name",
                "category",
                "rating",
                "total_user_ratings",
                "types",
                "formatted_address",
                "google_maps_url",
                "summary",
                "photo_name",
                "photo_count",
            ]
        )
    else:
        places_df = places_df.drop_duplicates(subset=["place_id"]).sort_values(
            by=["total_user_ratings", "rating"], ascending=[False, False], na_position="last"
        )

    reviews_df = pd.DataFrame(review_rows)
    if reviews_df.empty:
        reviews_df = pd.DataFrame(
            columns=["user_name", "place_id", "place_name", "rating", "review_text", "review_time"]
        )
    return places_df, reviews_df


def run_collection(config: ProjectConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    collector = GooglePlacesCollector(config)
    raw_pages, search_results = collector.fetch_places()
    detail_payloads = collector.fetch_place_details([row["id"] for row in search_results if row.get("id")])
    places_df, reviews_df = _normalize_places(detail_payloads, config.max_reviews_per_place)

    config.raw_places_json.write_text(json.dumps(raw_pages, indent=2, ensure_ascii=False))
    config.raw_details_json.write_text(json.dumps(detail_payloads, indent=2, ensure_ascii=False))
    places_df.to_csv(config.places_csv, index=False)
    reviews_df.to_csv(config.reviews_csv, index=False)
    return places_df, reviews_df


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Tenkasi tourism data from Google Places.")
    parser.add_argument(
        "--target-count",
        type=int,
        default=90,
        help="Maximum number of unique places to collect.",
    )
    parser.add_argument(
        "--pages-per-query",
        type=int,
        default=3,
        help="Maximum Google pagination depth per query.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = ProjectConfig(target_place_count=args.target_count, pages_per_query=args.pages_per_query)
    places_df, reviews_df = run_collection(config)
    print(f"Collected {len(places_df)} places and {len(reviews_df)} reviews.")


if __name__ == "__main__":
    main()
