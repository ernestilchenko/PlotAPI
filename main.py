import urllib3
from fastapi import FastAPI

from routers import parcels, buildings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(
    title="PlotAPI",
    description="API for searching Polish land parcels and buildings with export functionality. Created by ernestilchenko",
    version="1.1.0",
    contact={
        "name": "ernestilchenko",
        "url": "https://github.com/ernestilchenko"
    }
)

app.include_router(parcels.router, prefix="/api", tags=["Parcels"])
app.include_router(buildings.router, prefix="/api", tags=["Buildings"])


@app.get("/")
async def root():
    return {
        "message": "PlotAPI - Polish Land Parcel and Building Search API",
        "version": "1.1.0",
        "endpoints": {
            "parcels": "/api/parcel_by_id/",
            "buildings": "/api/building_by_id/"
        },
        "usage": {
            "search": "Add parcel_id or building_id parameter",
            "download": "Add format parameter (geojson, gml, kml, shp) to download file"
        },
        "supported_formats": ["geojson", "gml", "kml", "shp"]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
