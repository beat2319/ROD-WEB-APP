-- Enable PostGIS extension (required once per database)
CREATE EXTENSION IF NOT EXISTS postgis;

-- ROD aerial survey observations stored as MultiPolygon in EPSG:32604 (UTM Zone 4N)
CREATE TABLE rod_observations (
    id                  SERIAL PRIMARY KEY,
    objectid            INTEGER,
    created_date        BIGINT,        -- epoch milliseconds from GeoJSON
    feature_user_id     TEXT,
    region_id           INTEGER,
    host                TEXT,
    dca                 TEXT,          -- e.g. "unknown, suspected ROD"
    damage_type         TEXT,
    percent_affected    TEXT,
    collection_mode     TEXT,
    area_type           TEXT,
    photos              TEXT,
    acres               FLOAT,
    number_of_trees     TEXT,          -- count range string, e.g. "2-5"
    island              TEXT,
    year                TEXT,
    geom                geometry(MultiPolygon, 32604)
);

-- Coastline / vegetation reference layer stored as Polygon in EPSG:32604
CREATE TABLE coastline (
    id          SERIAL PRIMARY KEY,
    objectid    INTEGER,
    isle        TEXT,
    sqmi        FLOAT,
    water       INTEGER,
    geom        geometry(Polygon, 32604)
);

-- GIST spatial indexes for fast bounding-box and overlap queries
CREATE INDEX rod_geom_idx       ON rod_observations USING GIST(geom);
CREATE INDEX coastline_geom_idx ON coastline        USING GIST(geom);
