from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REFERENCE_DIR = DATA_DIR / "reference"
OUTPUTS_DIR = BASE_DIR / "outputs"
METRICS_DIR = OUTPUTS_DIR / "metrics"
PLOTS_DIR = OUTPUTS_DIR / "plots"
COMMUNITIES_DIR = OUTPUTS_DIR / "communities"
LINK_PREDICTION_DIR = OUTPUTS_DIR / "link_prediction"
GRAPHS_DIR = OUTPUTS_DIR / "graphs"
EXPORTS_DIR = OUTPUTS_DIR / "exports"
NEO4J_DIR = OUTPUTS_DIR / "neo4j"


DEFAULT_QUERIES = [
    "tourist attractions in Tenkasi",
    "hidden places in Tenkasi",
    "scenic places in Tenkasi",
    "waterfalls in Courtallam Tenkasi",
    "dams and parks in Tenkasi district",
    "heritage places in Tenkasi",
    "eco tourism places in Tenkasi",
    "trekking places in Tenkasi",
    "viewpoints in Tenkasi",
    "tourist places in Shenkottai Tenkasi",
    "tourist places in Kadayanallur Tenkasi",
    "tourist places in Sankarankovil Tenkasi",
    "tourist places in Alangulam Tenkasi",
    "tourist places in Sivagiri Tenkasi",
    "tourist places in Veerakeralampudur Tenkasi",
    "tourist places in Thiruvengadam Tenkasi",
    "tourist places in Surandai Tenkasi",
    "tourist places in Puliyangudi Tenkasi",
    "tourist places near Panpoli Tenkasi",
    "tourist places near Ilanji Tenkasi",
    "tourist places near Mekkarai Tenkasi",
]

DEFAULT_SEED_PLACES = [
    "Courtallam Main Falls",
    "Five Falls Courtallam",
    "Old Courtallam Falls",
    "Chitraruvi Courtallam",
    "Tiger Falls Courtallam",
    "Shenbagadevi Falls Courtallam",
    "Honey Falls Courtallam",
    "Fruit Garden Falls Courtallam",
    "Palaruvi Falls near Tenkasi",
    "Kutralanathar Temple Courtallam",
    "Chitra Sabha Courtallam",
    "Kasi Viswanathar Temple Tenkasi",
    "Thirumalai Kovil Panpoli",
    "Ilanji Kumaran Temple",
    "Pottalpudur Dargah",
    "Adavinainar Dam and Park",
    "Gundar Dam Tenkasi",
    "Gundar Falls Tenkasi",
    "Gadananathi Dam and Park",
    "Ramanathi Dam Tenkasi",
    "Karuppanathi Dam Tenkasi",
    "Manalar Falls Tenkasi",
    "Kutralanathar Temple",
    "Kurumpalanathar Temple Courtallam",
    "Sri Bhagavathy Amman Temple Courtallam",
    "Thiruvengadam temple Tenkasi",
    "Puliyangudi viewpoint Tenkasi",
    "Surandai scenic spot Tenkasi",
    "Achanputhur tourism spot Tenkasi",
    "Sundarapandiapuram Tenkasi",
    "Mekkarai Tenkasi",
    "Achankovil border route Tenkasi",
]


@dataclass(slots=True)
class ProjectConfig:
    api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_PLACES_API_KEY", ""))
    target_place_count: int = 160
    pages_per_query: int = 3
    max_reviews_per_place: int = 10
    text_queries: list[str] = field(default_factory=lambda: list(DEFAULT_QUERIES))
    seed_places: list[str] = field(default_factory=lambda: list(DEFAULT_SEED_PLACES))

    @property
    def places_csv(self) -> Path:
        return PROCESSED_DIR / "places.csv"

    @property
    def reviews_csv(self) -> Path:
        return PROCESSED_DIR / "reviews.csv"

    @property
    def edges_csv(self) -> Path:
        return PROCESSED_DIR / "edges.csv"

    @property
    def raw_places_json(self) -> Path:
        return RAW_DIR / "google_places_raw.json"

    @property
    def raw_details_json(self) -> Path:
        return RAW_DIR / "google_place_details.json"


def ensure_directories() -> None:
    for path in (
        RAW_DIR,
        PROCESSED_DIR,
        REFERENCE_DIR,
        OUTPUTS_DIR,
        METRICS_DIR,
        PLOTS_DIR,
        COMMUNITIES_DIR,
        LINK_PREDICTION_DIR,
        GRAPHS_DIR,
        EXPORTS_DIR,
        NEO4J_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
