import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List

import httpx

from config import settings
from .geometry_service import parse_gml_geometry_to_geojson


def _filter_xml(version: str, field: str, value: str) -> str:
    if version.startswith('2'):
        return f"<fes:Filter xmlns:fes='http://www.opengis.net/fes/2.0'><fes:PropertyIsEqualTo><fes:PropertyName>{field}</fes:PropertyName><fes:Literal>{value}</fes:Literal></fes:PropertyIsEqualTo></fes:Filter>"
    return f"<ogc:Filter xmlns:ogc='http://www.opengis.net/ogc'><ogc:PropertyIsEqualTo><ogc:PropertyName>{field}</ogc:PropertyName><ogc:Literal>{value}</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>"


def _build_params(layer: str, version: str, field: str, value: str, count: bool) -> Dict[str, str]:
    key = 'TYPENAMES' if version.startswith('2') else 'TYPENAME'
    p = {
        'SERVICE': 'WFS',
        'VERSION': version,
        'REQUEST': 'GetFeature',
        key: layer,
        'FILTER': _filter_xml(version, field, value)
    }
    if count:
        p['COUNT' if version.startswith('2') else 'MAXFEATURES'] = str(settings.MAX_FEATURES)
    return p


def _parse_features(xml_text: str) -> List[ET.Element]:
    root = ET.fromstring(xml_text.encode('utf-8'))
    tags = [
        '{http://www.opengis.net/wfs/2.0}member',
        '{http://www.opengis.net/gml}featureMember',
        '{http://www.opengis.net/gml/3.2}featureMember'
    ]
    members = []
    for t in tags:
        members.extend(root.findall(f'.//{t}'))
    return members


def _build_result(feature_member: ET.Element, entity_id: str) -> Optional[Dict[str, Any]]:
    feature = feature_member[0] if len(feature_member) else feature_member
    attrs = {}
    geom_xml = None
    for child in feature:
        name = child.tag.split('}')[-1]
        if any(g in name.lower() for g in ['geom', 'polygon', 'point', 'line', 'shape']):
            geom_xml = ET.tostring(child, encoding='unicode')
        elif name.lower() != 'boundedby':
            attrs[name] = child.text or ''
    if entity_id in str(attrs.values()):
        geojson = parse_gml_geometry_to_geojson(geom_xml) if geom_xml else None
        return {'attributes': attrs, 'geometry': geojson}
    return None


async def _try_request(client: httpx.AsyncClient, url: str, params: Dict[str, str]) -> Optional[str]:
    try:
        r = await client.get(url, params=params, timeout=settings.REQUEST_TIMEOUT)
        if r.status_code != 200:
            return None

        txt = r.text
        if 'ServiceException' in txt or 'ExceptionReport' in txt:
            p = {k: v for k, v in params.items() if k != 'FILTER'}
            p.update({'COUNT' if params['VERSION'].startswith('2') else 'MAXFEATURES': str(settings.MAX_FEATURES)})
            r = await client.get(url, params=p, timeout=settings.REQUEST_TIMEOUT)
            if r.status_code != 200:
                return None
            txt = r.text
        return txt
    except Exception:
        return None


async def _search_layer(url: str, layer: str, entity_id: str, field: str) -> Optional[Dict[str, Any]]:
    async with httpx.AsyncClient(verify=False) as client:
        for v in settings.WFS_VERSIONS:
            p = _build_params(layer, v, field, entity_id, False)
            txt = await _try_request(client, url, p)
            if not txt:
                continue
            for m in _parse_features(txt):
                res = _build_result(m, entity_id)
                if res:
                    return res
    return None


async def _search_layer_fallback_fields(url: str, layers: List[str], entity_id: str, fields: List[str]) -> Optional[
    Dict[str, Any]]:
    for layer in layers:
        for f in fields:
            res = await _search_layer(url, layer, entity_id, f)
            if res:
                return res
    return None


async def get_parcel_by_id(url: str, parcel_id: str) -> Optional[Dict[str, Any]]:
    fields = [settings.PARCEL_ID_FIELD] + settings.FALLBACK_PARCEL_ID_FIELDS
    return await _search_layer_fallback_fields(url, settings.PARCEL_LAYER_NAMES, parcel_id, fields)


async def get_building_by_id(url: str, building_id: str) -> Optional[Dict[str, Any]]:
    fields = [settings.BUILDING_ID_FIELD] + settings.FALLBACK_BUILDING_ID_FIELDS
    return await _search_layer_fallback_fields(url, settings.BUILDING_LAYER_NAMES, building_id, fields)
