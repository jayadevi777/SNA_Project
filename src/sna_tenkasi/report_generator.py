from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .config import OUTPUTS_DIR


TITLE = "DISCOVER THE CONNECTED TENKASI"
SUBTITLE = "A Social Network Analysis of Tourism in Tenkasi using User Interaction Data"
PDF_PATH = OUTPUTS_DIR / "Tenkasi_Tourism_SNA_Report.pdf"
ARCH_PATH = OUTPUTS_DIR / "tenkasi_architecture_colored.png"


ABSTRACT = (
    "Tenkasi, located in Tamil Nadu, is a tourism-rich region known not only for famous attractions such as Courtallam "
    "Falls and Kasi Viswanathar Temple, but also for many lesser-known scenic, cultural, eco-tourism, and pilgrimage "
    "destinations that remain structurally underrepresented in mainstream tourism systems. This project, titled Discover "
    "the Connected Tenkasi, applies Social Network Analysis (SNA) to study tourism in Tenkasi as an interaction-driven "
    "network rather than as a simple geographic catalogue of places. The project is designed as a full-scale data-driven "
    "tourism intelligence platform that uses Google Places API to collect place metadata, user reviews, ratings, and "
    "interaction signals, and transforms them into graph structures for analysis, visualization, and insight generation.\n\n"
    "The system models tourism places as nodes and relationships between them as edges derived from user behavior. Instead "
    "of focusing only on map coordinates, it emphasizes social and structural connectivity by building a user-place bipartite "
    "network, a place-place co-review network, and a user-user similarity network. In the user-place graph, an edge exists "
    "when a user reviews a destination. In the place-place graph, two destinations are connected if the same user has reviewed "
    "both, revealing shared visitor interest or probable co-visitation patterns. In the user-user graph, two users are linked "
    "when they review the same place, helping identify behavioral similarity among visitors. These graph models allow the "
    "project to capture hidden patterns of tourism movement, influence, clustering, and attraction-level importance across "
    "Tenkasi.\n\n"
    "The project is implemented as a full-stack analytical web platform with a Flask-based backend and a visualization-oriented "
    "frontend that presents destinations, network graphs, charts, centrality rankings, and tourism insights. The backend handles "
    "Google Places data collection, validation of more than one hundred tourism nodes, graph construction, SNA metric computation, "
    "and Neo4j export. The frontend serves as both an interactive tourism information portal and an analytical dashboard where users "
    "can view place relationships, network structure, top central nodes, community clusters, and chart-based summaries. By integrating "
    "API-driven tourism data with graph theory and web visualization, the project moves beyond static destination listing and provides "
    "an intelligent exploration layer for researchers, tourists, and regional planners.\n\n"
    "Several SNA metrics are applied to evaluate the role of each destination within the tourism ecosystem. Degree centrality identifies "
    "destinations with the highest number of direct network connections. Betweenness centrality reveals bridge nodes that connect otherwise "
    "separate clusters of tourism activity. Closeness centrality highlights destinations that can reach the rest of the graph efficiently, "
    "while PageRank evaluates importance based on the quality and influence of connected nodes. Extended metrics such as eigenvector centrality, "
    "Katz centrality, and HITS can also be incorporated to compare popularity with structural significance. These measures help identify whether "
    "a place is merely famous or whether it plays a central role in connecting different tourism circuits within Tenkasi.\n\n"
    "In addition to centrality analysis, the project studies the structural behavior of the tourism network using density, clustering coefficient, "
    "connected components, shortest path analysis, and degree distribution. Community detection methods such as Girvan-Newman and Louvain are used "
    "to identify natural clusters within the graph, such as waterfall groups, temple circuits, eco-tourism segments, or mixed hidden-destination "
    "communities. Link prediction methods including Common Neighbors, Jaccard Coefficient, and Adamic-Adar are applied to estimate potential future "
    "relationships between places. This predictive layer strengthens the project by moving from descriptive tourism analysis to recommendation-oriented "
    "network intelligence.\n\n"
    "The final outcome is a scalable and research-grade tourism SNA system that combines real-world data collection, graph construction, statistical "
    "and structural analysis, interactive visualization, and graph database compatibility through Neo4j. The system is suitable for MTech-level work "
    "in Artificial Intelligence and Data Science because it integrates API engineering, data preprocessing, graph analytics, predictive network modeling, "
    "and web-based interpretation into a single coherent platform. Overall, the project demonstrates how social network analysis can uncover hidden "
    "relationships, influential destinations, peripheral attractions, and structural tourism opportunities in Tenkasi, thereby enabling smarter tourism "
    "promotion and better regional planning."
)


OBJECTIVES = [
    "Collect and validate more than one hundred tourism-related places in Tenkasi using Google Places API.",
    "Extract place metadata including ratings, categories, review counts, addresses, and user reviews.",
    "Build a user-place bipartite graph to represent direct interaction between users and destinations.",
    "Construct a place-place network using shared reviewers to identify co-interest and likely co-visitation patterns.",
    "Construct a user-user network to model similarity among visitors based on common reviewed places.",
    "Generate node and edge datasets suitable for NetworkX analysis and Neo4j graph import.",
    "Compute SNA metrics such as degree centrality, betweenness centrality, closeness centrality, and PageRank.",
    "Detect communities and clusters among tourism destinations using graph-based community detection methods.",
    "Perform link prediction to identify likely future relationships between tourist places.",
    "Develop an interactive analytical website that presents graphs, charts, place information, and SNA insights.",
]


ARCH_OVERVIEW_ROWS = [
    ("Data Collection", "Google Places API, Python Requests", "Fetch Tenkasi places, reviews, ratings, categories, and details"),
    ("Data Processing", "Python, Pandas", "Clean, validate, normalize, and structure place and review data"),
    ("Graph Modeling", "NetworkX", "Build user-place, place-place, and user-user graphs"),
    ("SNA Engine", "NetworkX, Python", "Compute centrality, structure, communities, and link prediction"),
    ("Export Layer", "CSV, GEXF, JSON, Cypher", "Generate reusable graph and Neo4j import artifacts"),
    ("Web Application", "Flask, HTML, CSS, JavaScript", "Present dashboards, charts, rankings, and network insights"),
]


ARCH_NOTES = [
    "Frontend: Responsive tourism analytics website with dashboard, graphs, charts, places, reviews, community, and insights pages.",
    "Backend: Flask application serving datasets, analysis artifacts, graph exports, and visualization-ready outputs.",
    "Graph Data Model: Places and users are modeled as nodes, while reviewed, co-reviewed, and similarity relations form weighted edges.",
    "Neo4j Integration: CSV and Cypher export support enables graph-database import and advanced graph querying.",
]


METHODOLOGY = (
    "The methodology follows five phases: data collection, place validation, graph construction, SNA computation, and web-based visualization. "
    "In the first phase, the Google Places API is used to collect tourism-related places in Tenkasi using both generic tourism queries and "
    "curated seed destinations to ensure that hidden and underexplored places are included along with popular sites. In the second phase, the "
    "collected places are validated, cleaned, deduplicated, and ranked based on tourism relevance, rating information, review availability, "
    "and category quality. In the third phase, structured datasets are generated and transformed into a user-place bipartite graph, a place-place "
    "co-review graph, and a user-user similarity graph. In the fourth phase, NetworkX is used to compute degree centrality, betweenness centrality, "
    "closeness centrality, PageRank, structural statistics, community detection, and link prediction. In the final phase, the resulting graph outputs, "
    "charts, and rankings are visualized through a Flask-based tourism analytics website and exported to Neo4j-compatible graph files for extended graph exploration."
)


PSEUDOCODE = [
    "PROCEDURE BuildTourismGraphs(places, reviews):",
    "  userPlaceGraph = empty Graph",
    "  placePlaceGraph = empty Graph",
    "  userUserGraph = empty Graph",
    "",
    "  FOR EACH place p IN places DO",
    "    userPlaceGraph.addNode('place::' + p.place_id, {",
    "      name: p.place_name,",
    "      category: p.category,",
    "      rating: p.rating,",
    "      totalRatings: p.total_user_ratings",
    "    })",
    "  END FOR",
    "",
    "  FOR EACH review r IN reviews DO",
    "    userNode = 'user::' + normalize(r.user_name)",
    "    placeNode = 'place::' + r.place_id",
    "    userPlaceGraph.addNode(userNode, { name: r.user_name })",
    "    userPlaceGraph.addEdge(userNode, placeNode, {",
    "      type: 'reviewed',",
    "      reviewRating: r.rating,",
    "      reviewText: r.review_text",
    "    })",
    "  END FOR",
    "",
    "  FOR EACH user u IN userPlaceGraph.userNodes DO",
    "    reviewedPlaces = placesReviewedBy(u)",
    "    FOR EACH pair (p1, p2) IN combinations(reviewedPlaces, 2) DO",
    "      placePlaceGraph.addOrIncrementEdge(p1, p2, weight=1)",
    "    END FOR",
    "  END FOR",
    "",
    "  FOR EACH place p IN userPlaceGraph.placeNodes DO",
    "    reviewers = usersWhoReviewed(p)",
    "    FOR EACH pair (u1, u2) IN combinations(reviewers, 2) DO",
    "      userUserGraph.addOrIncrementEdge(u1, u2, weight=1)",
    "    END FOR",
    "  END FOR",
    "",
    "  RETURN userPlaceGraph, placePlaceGraph, userUserGraph",
    "END PROCEDURE",
    "",
    "PROCEDURE ComputeSNAMetrics(G):",
    "  FOR EACH node v IN G.nodes DO",
    "    v.degreeCentrality = DegreeCentrality(G, v)",
    "    v.betweennessCentrality = BetweennessCentrality(G, v)",
    "    v.closenessCentrality = ClosenessCentrality(G, v)",
    "    v.pageRank = PageRankScore(G, v)",
    "  END FOR",
    "  communitiesGN = GirvanNewman(G)",
    "  communitiesLouvain = LouvainCommunities(G)",
    "  predictedLinks = []",
    "  FOR EACH nonEdge (x, y) IN G.nonEdges DO",
    "    cn = CommonNeighbors(G, x, y)",
    "    jc = JaccardCoefficient(G, x, y)",
    "    aa = AdamicAdarIndex(G, x, y)",
    "    predictedLinks.append((x, y, cn, jc, aa))",
    "  END FOR",
    "  stats.density = NetworkDensity(G)",
    "  stats.connectedComponents = ConnectedComponents(G)",
    "  stats.clusteringCoeff = AverageClusteringCoefficient(G)",
    "  stats.shortestPaths = ShortestPathAnalysis(G)",
    "  RETURN nodeMetrics, communitiesGN, communitiesLouvain, predictedLinks, stats",
    "END PROCEDURE",
]


CONCLUSION = (
    "This project, Discover the Connected Tenkasi, demonstrates how Social Network Analysis can be used to transform tourism data into a structured "
    "intelligence system for regional tourism understanding and promotion. By modeling destinations and user interactions as graphs rather than as isolated "
    "records, the project reveals influential places, hidden connectors, community clusters, and emerging co-visit patterns across Tenkasi. The system combines "
    "Google Places API collection, graph construction, NetworkX-based SNA computation, Neo4j export, and a Flask-based analytical website into one complete framework. "
    "The result is not only a tourism portal, but also a scalable decision-support platform for researchers, planners, and visitors. In essence, the project turns "
    "Tenkasi from a list of attractions into a connected tourism network that can be analyzed, visualized, and interpreted with scientific rigor."
)


def _page():
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _header(ax, section: str) -> None:
    ax.text(0.06, 0.965, TITLE, fontsize=20, weight="bold", color="#17212b", va="top")
    ax.text(0.06, 0.935, SUBTITLE, fontsize=12.5, color="#334155", va="top")
    ax.text(0.06, 0.892, section, fontsize=15.5, weight="bold", color="#0f766e", va="top")
    ax.plot([0.06, 0.94], [0.878, 0.878], color="#cbd5e1", lw=1.2)


def _draw_text_block(ax, text: str, x: float, y: float, width: int, size: float, spacing: float = 1.28) -> None:
    paragraphs = text.split("\n\n")
    current_y = y
    for para in paragraphs:
        wrapped = textwrap.fill(para, width=width)
        ax.text(x, current_y, wrapped, fontsize=size, color="#111827", va="top", ha="left", linespacing=spacing)
        lines = wrapped.count("\n") + 1
        current_y -= lines * 0.0205 * (size / 11.0) * spacing
        current_y -= 0.016


def _draw_bullets(ax, bullets: list[str], x: float, y: float, width: int, size: float, gap: float) -> None:
    cy = y
    for bullet in bullets:
        wrapped = textwrap.fill("\u2022 " + bullet, width=width)
        ax.text(x, cy, wrapped, fontsize=size, color="#111827", va="top", ha="left", linespacing=1.25)
        cy -= (wrapped.count("\n") + 1) * gap


def generate_architecture_image(output_path: Path = ARCH_PATH) -> Path:
    fig, ax = plt.subplots(figsize=(15, 9))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")

    palette = {
        "green": ("#0f766e", "#d9f7f1"),
        "blue": ("#2563eb", "#e0ecff"),
        "amber": ("#d97706", "#fff1d6"),
        "violet": ("#7c3aed", "#f0e4ff"),
        "rose": ("#be123c", "#ffe3ec"),
    }

    boxes = [
        ("Google Places API\nText Search + Place Details", 0.7, 7.0, 2.9, 1.2, "green"),
        ("Raw JSON Storage\nPlaces + Reviews Payloads", 4.0, 7.0, 2.7, 1.2, "blue"),
        ("Data Validation and Cleaning\nDeduplication, Scoring, Filtering", 7.1, 7.0, 3.2, 1.2, "amber"),
        ("Structured Datasets\nplaces.csv  reviews.csv  edges.csv", 10.8, 7.0, 3.4, 1.2, "violet"),
        ("User-Place Graph\nBipartite Interaction Model", 0.9, 4.7, 2.8, 1.2, "rose"),
        ("Place-Place Graph\nCo-review Network", 4.2, 4.7, 2.7, 1.2, "green"),
        ("User-User Graph\nSimilarity Network", 7.3, 4.7, 2.7, 1.2, "blue"),
        ("SNA Analytics Core\nCentrality + Structure + Communities + Link Prediction", 10.3, 4.5, 4.0, 1.6, "amber"),
        ("Visualization Layer\nPlots + Charts + Network Graphs", 2.0, 1.8, 3.2, 1.2, "violet"),
        ("Neo4j Export Layer\nCSV + Cypher Import", 6.0, 1.8, 3.0, 1.2, "rose"),
        ("Flask Web Application\nDashboard + Analysis + Insights", 9.9, 1.8, 3.8, 1.2, "green"),
    ]

    for label, x, y, w, h, key in boxes:
        edge, fill = palette[key]
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            linewidth=2.2, edgecolor=edge, facecolor=fill
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11, weight="bold", color="#17212b")

    arrows = [
        ((3.6, 7.6), (4.0, 7.6)),
        ((6.7, 7.6), (7.1, 7.6)),
        ((10.3, 7.6), (10.8, 7.6)),
        ((2.2, 7.0), (2.2, 5.9)),
        ((5.5, 7.0), (5.5, 5.9)),
        ((8.6, 7.0), (8.6, 5.9)),
        ((12.5, 7.0), (12.3, 6.1)),
        ((3.7, 5.3), (4.2, 5.3)),
        ((6.9, 5.3), (7.3, 5.3)),
        ((10.0, 5.3), (10.3, 5.3)),
        ((12.3, 4.5), (12.3, 3.0)),
        ((5.2, 2.4), (6.0, 2.4)),
        ((9.0, 2.4), (9.9, 2.4)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16, linewidth=2.0, color="#64748b"))

    ax.text(0.7, 8.55, "System Architecture of the Tenkasi Tourism SNA Platform", fontsize=19, weight="bold", color="#17212b")
    ax.text(0.7, 8.18, "Pipeline for data acquisition, graph modeling, network analytics, Neo4j export, and web visualization", fontsize=11.5, color="#475569")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _draw_architecture_table(ax, x: float, y: float) -> None:
    col_x = [x, x + 0.20, x + 0.50]
    row_h = 0.045
    headers = ["Layer", "Technology", "Responsibility"]
    ax.add_patch(plt.Rectangle((x, y - row_h), 0.84, row_h, facecolor="#d9f7f1", edgecolor="#94a3b8", lw=1))
    for i, h in enumerate(headers):
        ax.text(col_x[i] + 0.005, y - 0.012, h, fontsize=10.5, weight="bold", va="top", color="#17212b")
    cy = y - row_h
    fills = ["#ffffff", "#f8fafc"]
    for idx, row in enumerate(ARCH_OVERVIEW_ROWS):
        cy -= row_h
        ax.add_patch(plt.Rectangle((x, cy), 0.84, row_h, facecolor=fills[idx % 2], edgecolor="#cbd5e1", lw=0.8))
        ax.text(col_x[0] + 0.005, cy + row_h - 0.010, row[0], fontsize=9.5, va="top", color="#17212b")
        ax.text(col_x[1] + 0.005, cy + row_h - 0.010, textwrap.fill(row[1], 28), fontsize=9.2, va="top", color="#17212b")
        ax.text(col_x[2] + 0.005, cy + row_h - 0.010, textwrap.fill(row[2], 38), fontsize=9.2, va="top", color="#17212b")


def generate_project_pdf(pdf_path: Path = PDF_PATH) -> Path:
    arch_path = generate_architecture_image()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(pdf_path) as pdf:
        fig, ax = _page()
        _header(ax, "ABSTRACT")
        _draw_text_block(ax, ABSTRACT, 0.06, 0.855, 118, 10.3, 1.24)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = _page()
        _header(ax, "OBJECTIVES")
        _draw_bullets(ax, OBJECTIVES, 0.07, 0.85, 110, 11.2, 0.052)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = _page()
        _header(ax, "SYSTEM ARCHITECTURE")
        ax.text(0.06, 0.848, "The project follows a multi-layer analytical architecture with a clear separation between data collection, graph modeling, analytics, visualization, and graph database export. The system is centered on a Flask-based backend that acquires and processes Google Places data, computes SNA metrics using Python graph libraries, and serves outputs to a tourism analytics website.", fontsize=10.3, color="#111827", va="top")
        ax.text(0.06, 0.802, "Architecture Overview", fontsize=12.2, weight="bold", color="#17212b", va="top")
        _draw_architecture_table(ax, 0.06, 0.782)
        ax.text(0.06, 0.43, "Component Breakdown", fontsize=12.2, weight="bold", color="#17212b", va="top")
        _draw_bullets(ax, ARCH_NOTES, 0.07, 0.405, 110, 10.2, 0.048)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = _page()
        _header(ax, "SYSTEM ARCHITECTURE DIAGRAM")
        img = plt.imread(arch_path)
        ax.imshow(img, extent=[0.05, 0.95, 0.09, 0.86], aspect="auto")
        ax.axis("off")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = _page()
        _header(ax, "METHODOLOGY & PSEUDOCODE")
        ax.text(0.06, 0.848, "Methodology", fontsize=12.2, weight="bold", color="#17212b", va="top")
        _draw_text_block(ax, METHODOLOGY, 0.06, 0.825, 118, 10.5, 1.22)
        ax.text(0.06, 0.57, "Graph Construction and SNA Computation — Pseudocode", fontsize=12.2, weight="bold", color="#17212b", va="top")
        y = 0.545
        for line in PSEUDOCODE:
            ax.text(0.07, y, line, fontsize=8.9, family="monospace", color="#111827", va="top")
            y -= 0.0152
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = _page()
        _header(ax, "CONCLUSION")
        _draw_text_block(ax, CONCLUSION, 0.06, 0.855, 118, 11.0, 1.28)
        ax.text(0.06, 0.18, "FINAL GITHUB REPO LINK:", fontsize=11.5, weight="bold", color="#17212b", va="top")
        ax.text(0.06, 0.145, "<add your repository link here>", fontsize=11.0, color="#2563eb", va="top")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    return pdf_path


def main() -> None:
    path = generate_project_pdf()
    print(path)


if __name__ == "__main__":
    main()
