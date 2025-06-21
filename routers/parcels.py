from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from config import settings
from models import ParcelResponse, ErrorResponse, ParcelData, ServiceInfo
from services import get_parcel_by_id
from services.export_service import get_export_data
from utils import get_teryt_from_id, find_service_by_teryt

router = APIRouter()


@router.get("/parcel_by_id/", response_model=None, responses={404: {"model": ErrorResponse}})
async def search_parcel_by_id(
        parcel_id: str = Query(..., description="Parcel ID to search for"),
        format: Optional[str] = Query(None, description="Export format: geojson, gml, kml, shp",
                                      regex="^(geojson|gml|kml|shp)$")
):
    teryt = get_teryt_from_id(parcel_id)
    service = find_service_by_teryt(settings.WFS_DATA_FILE, teryt)

    if not service:
        raise HTTPException(status_code=404, detail=f"No WFS service found for TERYT code: {teryt}")

    parcel = get_parcel_by_id(service['url'], parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel with ID {parcel_id} not found in any available layer")

    if format:
        try:
            content, media_type, filename = get_export_data(parcel, parcel_id, "parcel", format)

            return Response(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    return ParcelResponse(
        status="success",
        parcel_id=parcel_id,
        teryt=teryt,
        service=ServiceInfo(
            organization=service['organization'],
            url=service['url']
        ),
        data=ParcelData(
            attributes=parcel['attributes'],
            geometry=parcel['geometry']
        )
    )
