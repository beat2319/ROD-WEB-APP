import json
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]


def _get_conn():
    """Return a psycopg2 connection using DATABASE_URL from the environment."""
    return psycopg2.connect(DATABASE_URL)


def _ingest_rod(cur, features: list) -> int:
    """Insert ROD observation features into the rod_observations table."""
    sql = """
        INSERT INTO rod_observations (
            objectid, created_date, feature_user_id, region_id, host,
            dca, damage_type, percent_affected, collection_mode, area_type,
            photos, acres, number_of_trees, island, year, geom
        ) VALUES (
            %(objectid)s, %(created_date)s, %(feature_user_id)s, %(region_id)s, %(host)s,
            %(dca)s, %(damage_type)s, %(percent_affected)s, %(collection_mode)s, %(area_type)s,
            %(photos)s, %(acres)s, %(number_of_trees)s, %(island)s, %(year)s,
            ST_Multi(ST_GeomFromGeoJSON(%(geom)s)) -- <-- Add ST_Multi() here
        )
    """
    rows = []
    for f in features:
        p = f["properties"]
        rows.append({
            "objectid":          p.get("OBJECTID"),
            "created_date":      p.get("CREATED_DATE"),
            "feature_user_id":   p.get("FEATURE_USER_ID"),
            "region_id":         p.get("REGION_ID"),
            "host":              p.get("HOST"),
            "dca":               p.get("DCA"),
            "damage_type":       p.get("DAMAGE_TYPE"),
            "percent_affected":  p.get("PERCENT_AFFECTED"),
            "collection_mode":   p.get("COLLECTION_MODE"),
            "area_type":         p.get("AREA_TYPE"),
            "photos":            p.get("PHOTOS"),
            "acres":             p.get("ACRES"),
            "number_of_trees":   p.get("NUMBER_OF_TREES_COUNT_RANGE"),
            "island":            p.get("ISLAND"),
            "year":              p.get("YEAR"),
            "geom":              json.dumps(f["geometry"]),
        })
    cur.executemany(sql, rows)
    return len(rows)


def _ingest_coastline(cur, features: list) -> int:
    """Insert coastline features into the coastline table."""
    sql = """
        INSERT INTO coastline (objectid, isle, sqmi, water, geom)
        VALUES (%(objectid)s, %(isle)s, %(sqmi)s, %(water)s, ST_GeomFromGeoJSON(%(geom)s))
    """
    rows = []
    for f in features:
        p = f["properties"]
        rows.append({
            "objectid": p.get("objectid"),
            "isle":     p.get("isle"),
            "sqmi":     p.get("sqmi"),
            "water":    p.get("water"),
            "geom":     json.dumps(f["geometry"]),
        })
    cur.executemany(sql, rows)
    return len(rows)


def ingest_geojson(geojson: dict, layer: str) -> int:
    """Route a GeoJSON FeatureCollection to the correct table based on layer name."""
    features = geojson.get("features", [])
    with _get_conn() as conn:
        with conn.cursor() as cur:
            if layer == "rod":
                return _ingest_rod(cur, features)
            elif layer == "coastline":
                return _ingest_coastline(cur, features)
            else:
                raise ValueError(f"Unknown layer: {layer}")
