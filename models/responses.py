from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class ServiceInfo(BaseModel):
    organization: str
    url: str


class GeometryResponse(BaseModel):
    type: str
    coordinates: List[Any]


class ParcelData(BaseModel):
    attributes: Dict[str, str]
    geometry: Optional[GeometryResponse]


class BuildingData(BaseModel):
    attributes: Dict[str, str]
    geometry: Optional[GeometryResponse]


class ParcelResponse(BaseModel):
    status: str
    parcel_id: str
    teryt: str
    service: ServiceInfo
    data: ParcelData


class BuildingResponse(BaseModel):
    status: str
    building_id: str
    teryt: str
    service: ServiceInfo
    data: BuildingData


class ErrorResponse(BaseModel):
    detail: str
