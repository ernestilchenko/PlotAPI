from fastapi import APIRouter, HTTPException, Query
from models import ParcelResponse, ErrorResponse, ParcelData, ServiceInfo
from services import get_parcel_by_id
from utils import get_teryt_from_id, find_service_by_teryt
from config import settings

router = APIRouter()


@router.get("/parcel_by_id/", response_model=ParcelResponse, responses={404: {"model": ErrorResponse}})
async def search_parcel_by_id(parcel_id: str = Query(..., description="Parcel ID to search for")):
    teryt = get_teryt_from_id(parcel_id)
    service = find_service_by_teryt(settings.WFS_DATA_FILE, teryt)

    if not service:
        raise HTTPException(status_code=404, detail=f"No WFS service found for TERYT code: {teryt}")

    parcel = get_parcel_by_id(service['url'], parcel_id)
    if parcel:
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
    else:
        raise HTTPException(status_code=404, detail=f"Parcel with ID {parcel_id} not found in any available layer")