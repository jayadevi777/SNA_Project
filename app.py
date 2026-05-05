from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template, request, send_from_directory

from src.sna_tenkasi.web import load_dashboard_data


app = Flask(__name__)


def artifact_url(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return f"/artifacts/{path.relative_to(Path.cwd()).as_posix()}"


@app.context_processor
def inject_globals():
    return {"artifact_url": artifact_url}


@app.route("/artifacts/<path:filename>")
def artifacts(filename: str):
    return send_from_directory(Path.cwd(), filename)


@app.route("/")
def home():
    data = load_dashboard_data()
    return render_template("home.html", data=data)


@app.route("/analytics")
def analytics():
    data = load_dashboard_data()
    active_tab = request.args.get("tab", "overview")
    metric = request.args.get("metric", "degree")
    return render_template("analytics.html", data=data, active_tab=active_tab, metric=metric)


@app.route("/recommendations")
def recommendations():
    data = load_dashboard_data()
    return render_template("recommendations.html", data=data)


@app.route("/places")
def places():
    data = load_dashboard_data()
    return render_template("places.html", data=data)


@app.route("/graphs")
def graphs():
    data = load_dashboard_data()
    return render_template("graphs.html", data=data)


@app.route("/exports")
def exports():
    data = load_dashboard_data()
    return render_template("exports.html", data=data)


if __name__ == "__main__":
    app.run(debug=True)
