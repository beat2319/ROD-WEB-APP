import json
import os
import psycopg2
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="ROD Listener")

# Allow the MapBox frontend to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
DATABASE_URL = os.environ["DATABASE_URL"]


def _get_conn():
    """Return a psycopg2 connection using DATABASE_URL from the environment."""
    return psycopg2.connect(DATABASE_URL)


def _rows_to_feature_collection(rows: list) -> dict:
    """Convert (properties_json, geometry_json) rows into a GeoJSON FeatureCollection."""
    features = [
        {"type": "Feature", "properties": props, "geometry": json.loads(geom)}
        for props, geom in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@app.get("/rod")
def get_rod(island: str = Query(None), year: str = Query(None)):
    """Return ROD observations as GeoJSON, optionally filtered by island and/or year."""
    where, params = [], []
    if island:
        where.append("island = %s")
        params.append(island)
    if year:
        where.append("year = %s")
        params.append(year)

    clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT row_to_json(t) - 'geom', ST_AsGeoJSON(ST_Transform(geom, 4326))
        FROM (
            SELECT id, objectid, created_date, feature_user_id, region_id,
                   host, dca, damage_type, percent_affected, collection_mode,
                   area_type, photos, acres, number_of_trees, island, year, geom
            FROM rod_observations {clause}
        ) t
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return JSONResponse(_rows_to_feature_collection(rows))


@app.get("/rod/bbox")
def get_rod_bbox(minx: float, miny: float, maxx: float, maxy: float):
    """Return ROD observations that intersect the given WGS84 bounding box."""
    sql = """
        SELECT row_to_json(t) - 'geom', ST_AsGeoJSON(ST_Transform(geom, 4326))
        FROM (
            SELECT id, objectid, island, year, damage_type, acres, geom
            FROM rod_observations
            WHERE ST_Intersects(
                ST_Transform(geom, 4326),
                ST_MakeEnvelope(%s, %s, %s, %s, 4326)
            )
        ) t
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [minx, miny, maxx, maxy])
            rows = cur.fetchall()

    return JSONResponse(_rows_to_feature_collection(rows))


@app.get("/coastline")
def get_coastline():
    """Return the full coastline / vegetation reference layer as GeoJSON."""
    sql = """
        SELECT row_to_json(t) - 'geom', ST_AsGeoJSON(ST_Transform(geom, 4326))
        FROM (
            SELECT id, objectid, isle, sqmi, water, geom
            FROM coastline
        ) t
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return JSONResponse(_rows_to_feature_collection(rows))


@app.get("/tiles/rod/{z}/{x}/{y}")
def tiles_rod(z: int, x: int, y: int):
    """Return ROD observations as a Mapbox Vector Tile (MVT) for the given z/x/y coordinate."""
    sql = """
        SELECT ST_AsMVT(tile, 'rod', 4096, 'mvt_geom')
        FROM (
            SELECT
                id, island, year, damage_type, acres,
                ST_AsMVTGeom(
                    ST_Transform(geom, 3857),
                    ST_TileEnvelope(%s, %s, %s),
                    4096, 256, true
                ) AS mvt_geom
            FROM rod_observations
            WHERE ST_Intersects(ST_Transform(geom, 3857), ST_TileEnvelope(%s, %s, %s))
        ) tile
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [z, x, y, z, x, y])
            tile_bytes = cur.fetchone()[0].tobytes()

    return Response(content=tile_bytes, media_type="application/x-protobuf")


@app.get("/tiles/coastline/{z}/{x}/{y}")
def tiles_coastline(z: int, x: int, y: int):
    """Return the coastline layer as a Mapbox Vector Tile (MVT) for the given z/x/y coordinate."""
    sql = """
        SELECT ST_AsMVT(tile, 'coastline', 4096, 'mvt_geom')
        FROM (
            SELECT
                id, isle, sqmi,
                ST_AsMVTGeom(
                    ST_Transform(geom, 3857),
                    ST_TileEnvelope(%s, %s, %s),
                    4096, 256, true
                ) AS mvt_geom
            FROM coastline
            WHERE ST_Intersects(ST_Transform(geom, 3857), ST_TileEnvelope(%s, %s, %s))
        ) tile
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [z, x, y, z, x, y])
            tile_bytes = cur.fetchone()[0].tobytes()

    return Response(content=tile_bytes, media_type="application/x-protobuf")
