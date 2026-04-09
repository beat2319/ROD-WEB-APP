import json
from google.cloud import storage
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ingest import ingest_geojson

app = FastAPI(title="ROD Worker")


class WebhookPayload(BaseModel):
    bucket: str
    blob: str
    layer: str  # "rod" or "coastline"


@app.post("/webhook")
def receive_webhook(payload: WebhookPayload):
    """Connect to GCS, download the named blob as GeoJSON, and ingest it into PostGIS."""
    client = storage.Client()
    bucket = client.bucket(payload.bucket)
    blob = bucket.blob(payload.blob)

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"Blob {payload.blob} not found in {payload.bucket}")

    geojson = json.loads(blob.download_as_text())
    count = ingest_geojson(geojson, payload.layer)
    return {"status": "ok", "features_ingested": count}
