import io
import json
import os
from datetime import datetime
from flask import Flask, request, render_template, jsonify, abort, send_file
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import Base, get_engine, Location, Query, Observation
from services.provider import (
    geocode_location,
    get_current_weather_openweather,
    get_forecast_openweather,
    get_historical_open_meteo,
)
from services.util import parse_date, validate_date_range, to_csv_bytes

load_dotenv()

# Helper functions
def resolve_location(q, lat, lon):
    if not (q or (lat and lon)):
        return None, {"error": "Provide ?q=location OR ?lat=..&lon=.."}, 400
    if q:
        geo = geocode_location(q)
        if not geo:
            return None, {"error": "Location not found"}, 404
        return (geo["latitude"], geo["longitude"]), None, None
    return (float(lat), float(lon)), None, None

def require_api_key(app):
    api_key = app.config.get("OPENWEATHER_API_KEY")
    if not api_key:
        return None, {"error": "Missing OPENWEATHER_API_KEY"}, 500
    return api_key, None, None

def add_observations(session, query_id, lat, lon, start_date, end_date):
    hist = get_historical_open_meteo(lat, lon, start_date, end_date)
    for row in hist:
        d = parse_date(row["date"])
        session.add(
            Observation(
                query_id=query_id,
                query_date=d,
                t_min=row["t_min"],
                t_max=row["t_max"],
                t_mean=row["t_mean"],
            )
        )

def create_app():
    app = Flask(__name__)
    app.config["OPENWEATHER_API_KEY"] = os.getenv("OPENWEATHER_API_KEY", "").strip()

    engine = get_engine()
    Base.metadata.create_all(engine)

    @app.cli.command("db-init")
    def db_init():
        Base.metadata.create_all(engine)
        print("Database initialized.")

    @app.route("/")
    def home():
        with Session(engine) as s:
            queries = (
                s.execute(select(Query).order_by(Query.created_at.desc()).limit(10))
                .scalars()
                .all()
            )
        return render_template("index.html", queries=queries)

    # Weather APIs
    @app.get("/api/weather/current")
    def api_current():
        coords, err, code = resolve_location(
            request.args.get("q"),
            request.args.get("lat"),
            request.args.get("lon")
        )
        if err:
            return jsonify(err), code

        api_key, err, code = require_api_key(app)
        if err:
            return jsonify(err), code

        lat, lon = coords
        data = get_current_weather_openweather(lat, lon, api_key)
        return jsonify(data)

    @app.get("/api/weather/forecast")
    def api_forecast():
        coords, err, code = resolve_location(
            request.args.get("q"),
            request.args.get("lat"),
            request.args.get("lon")
        )
        if err:
            return jsonify(err), code

        api_key, err, code = require_api_key(app)
        if err:
            return jsonify(err), code

        lat, lon = coords
        data = get_forecast_openweather(float(lat), float(lon), api_key)
        return jsonify(data)

    # CRUD
    @app.post("/api/queries")
    def create_query():
        payload = request.get_json(force=True, silent=True) or {}
        location_text = (payload.get("location") or "").strip()
        start_s = payload.get("start_date")
        end_s = payload.get("end_date")

        if not location_text:
            return jsonify({"error": "location is required"}), 400

        start_date = parse_date(start_s)
        end_date = parse_date(end_s)
        ok, msg = validate_date_range(start_date, end_date)
        if not ok:
            return jsonify({"error": msg}), 400

        geo = geocode_location(location_text)
        if not geo:
            return jsonify({"error": "Location not found"}), 404

        with Session(engine) as s:
            loc = (
                s.query(Location)
                .filter_by(latitude=geo["latitude"], longitude=geo["longitude"])
                .first()
            )
            if not loc:
                loc = Location(
                    name=geo.get("name") or location_text,
                    country=geo.get("country"),
                    latitude=geo["latitude"],
                    longitude=geo["longitude"],
                )
                s.add(loc)
                s.flush()

            q = Query(location_id=loc.id, start_date=start_date, end_date=end_date)
            s.add(q)
            s.flush()

            add_observations(s, q.id, loc.latitude, loc.longitude, start_date, end_date)
            s.commit()

            return jsonify(q.to_dict(with_observations=True)), 201

    @app.get("/api/queries")
    def list_queries():
        with Session(engine) as s:
            queries = s.query(Query).order_by(Query.created_at.desc()).all()
            return jsonify([q.to_dict() for q in queries])

    @app.get("/api/queries/<int:qid>")
    def get_query(qid: int):
        with Session(engine) as s:
            q = s.get(Query, qid)
            if not q:
                return jsonify({"error": "Not found"}), 404
            return jsonify(q.to_dict(with_observations=True))

    @app.put("/api/queries/<int:qid>")
    def update_query(qid: int):
        payload = request.get_json(force=True, silent=True) or {}
        with Session(engine) as s:
            q = s.get(Query, qid)
            if not q:
                return jsonify({"error": "Not found"}), 404

            if "location" in payload and payload["location"]:
                geo = geocode_location(payload["location"])
                if not geo:
                    return jsonify({"error": "Location not found"}), 404
                loc = (
                    s.query(Location)
                    .filter_by(latitude=geo["latitude"], longitude=geo["longitude"])
                    .first()
                )
                if not loc:
                    loc = Location(
                        name=geo.get("name") or payload["location"],
                        country=geo.get("country"),
                        latitude=geo["latitude"],
                        longitude=geo["longitude"],
                    )
                    s.add(loc)
                    s.flush()
                q.location_id = loc.id

            sd = parse_date(payload.get("start_date")) or q.start_date
            ed = parse_date(payload.get("end_date")) or q.end_date
            ok, msg = validate_date_range(sd, ed)
            if not ok:
                return jsonify({"error": msg}), 400
            q.start_date, q.end_date = sd, ed

            s.query(Observation).where(Observation.query_id == q.id).delete(
                synchronize_session=False
            )
            loc = s.get(Location, q.location_id)

            add_observations(s, q.id, loc.latitude, loc.longitude, q.start_date, q.end_date)

            s.commit()
            return jsonify(q.to_dict(with_observations=True))

    @app.delete("/api/queries/<int:qid>")
    def delete_query(qid: int):
        with Session(engine) as s:
            q = s.get(Query, qid)
            if not q:
                return jsonify({"error": "Not found"}), 404
            s.query(Observation).where(Observation.query_id == q.id).delete(
                synchronize_session=False
            )
            s.delete(q)
            s.commit()
            return jsonify({"status": "deleted", "id": qid})

    @app.get("/export.<fmt>")
    def export(fmt: str):
        fmt = fmt.lower()
        if fmt not in {"json", "csv"}:
            abort(400, "fmt must be json or csv")

        with Session(engine) as s:
            queries = s.query(Query).order_by(Query.id.asc()).all()
            data = [q.to_dict(with_observations=True) for q in queries]

        if fmt == "json":
            payload = json.dumps(data, default=str, indent=2).encode("utf-8")
            return send_file(
                io.BytesIO(payload),
                mimetype="application/json",
                as_attachment=True,
                download_name="export.json",
            )
        else:
            csv_bytes = to_csv_bytes(data)
            return send_file(
                io.BytesIO(csv_bytes),
                mimetype="text/csv",
                as_attachment=True,
                download_name="export.csv",
            )

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
