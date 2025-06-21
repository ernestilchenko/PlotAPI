from fastapi import APIRouter, HTTPException, Query
from models import BuildingResponse, ErrorResponse, BuildingData, ServiceInfo
from services import get_building_by_id
from utils import get_teryt_from_id, find_service_by_teryt
from config import settings

router = APIRouter()


@router.get("/building_by_id/", response_model=BuildingResponse, responses={404: {"model": ErrorResponse}})
async def search_building_by_id(building_id: str = Query(..., description="Building ID to search for")):
    teryt = get_teryt_from_id(building_id)
    service = find_service_by_teryt(settings.WFS_DATA_FILE, teryt)

    if not service:
        raise HTTPException(status_code=404, detail=f"No WFS service found for TERYT code: {teryt}")

    building = get_building_by_id(service['url'], building_id)
    if building:
        return BuildingResponse(
            status="success",
            building_id=building_id,
            teryt=teryt,
            service=ServiceInfo(
                organization=service['organization'],
                url=service['url']
            ),
            data=BuildingData(
                attributes=building['attributes'],
                geometry=building['geometry']
            )
        )
    else:
        raise HTTPException(status_code=404, detail=f"Building with ID {building_id} not found in any available layer")