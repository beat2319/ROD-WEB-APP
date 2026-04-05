![backend_design](../attachments/png/ROD-User-Server.png)

- Our planned backend design utilizes **PostGIS SQL functions** to serve **Mapbox Vector Tiles** (MVT). A **worker** process will collect predicted detections in .geojson format from a **Google Cloud bucket** and insert them into the **PostGIS database**.
- Functions to convert spatial data to a Geojson (works in google sql)
	- [ST_AsGeoJSON](https://postgis.net/docs/ST_AsGeoJSON.html)
	- Will Beach