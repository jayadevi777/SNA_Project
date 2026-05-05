# Tenkasi Tourism SNA

Social Network Analysis project on tourism in Tenkasi using Google Places user interaction data, NetworkX, Neo4j, and Flask.

## Requirements

- Python 3
- Google Places API key
- Neo4j

## Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Add your credentials in `.env`:

```env
GOOGLE_PLACES_API_KEY=your_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## Run Data Collection

```bash
python3 -m src.sna_tenkasi.collector --target-count 160 --pages-per-query 3
```

## Run Analysis Pipeline

```bash
python3 -m src.sna_tenkasi.pipeline --collect --export-neo4j --import-neo4j
```

## Run Website

```bash
flask --app app run
```

If port `5000` is busy:

```bash
flask --app app run --port 5001
```

## Pages

- `/` Home
- `/analytics` Network analysis
- `/recommendations` Recommendation system
- `/places` Places explorer
- `/graphs` Graph visualization
- `/exports` Export files

## Project Structure

```text
SNA/
├── app.py
├── requirements.txt
├── .env.example
├── tenkasi_api.py
├── src/sna_tenkasi/
├── templates/
├── static/
├── data/
├── outputs/
└── docs/
```
