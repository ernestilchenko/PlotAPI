import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List

import requests

from config import settings
from .geometry_service import parse_gml_geometry_to_geojson


def get_feature_by_id_qgis_style(url: str, layer_name: str, entity_id: str, id_field: str) -> Optional[Dict[str, Any]]:
    session = requests.Session()
    session.verify = False

    versions = ['1.0.0', '1.1.0', '2.0.0']

    for version in versions:
        if version == '1.0.0':
            params = {
                'SERVICE': 'WFS',
                'VERSION': version,
                'REQUEST': 'GetFeature',
                'TYPENAME': layer_name,
                'FILTER': f"<ogc:Filter xmlns:ogc='http://www.opengis.net/ogc'><ogc:PropertyIsEqualTo><ogc:PropertyName>{id_field}</ogc:PropertyName><ogc:Literal>{entity_id}</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>"
            }
        elif version == '1.1.0':
            params = {
                'SERVICE': 'WFS',
                'VERSION': version,
                'REQUEST': 'GetFeature',
                'TYPENAME': layer_name,
                'FILTER': f"<ogc:Filter xmlns:ogc='http://www.opengis.net/ogc'><ogc:PropertyIsEqualTo><ogc:PropertyName>{id_field}</ogc:PropertyName><ogc:Literal>{entity_id}</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>"
            }
        else:
            params = {
                'SERVICE': 'WFS',
                'VERSION': version,
                'REQUEST': 'GetFeature',
                'TYPENAMES': layer_name,
                'FILTER': f"<fes:Filter xmlns:fes='http://www.opengis.net/fes/2.0'><fes:PropertyIsEqualTo><fes:PropertyName>{id_field}</fes:PropertyName><fes:Literal>{entity_id}</fes:Literal></fes:PropertyIsEqualTo></fes:Filter>"
            }

        try:
            response = session.get(url, params=params, timeout=settings.REQUEST_TIMEOUT)

            if response.status_code == 200:
                response.encoding = 'utf-8'
                content = response.text

                if 'ServiceException' in content or 'ExceptionReport' in content:
                    print("Service exception - trying without filter...")

                    params_no_filter = params.copy()
                    if 'FILTER' in params_no_filter:
                        del params_no_filter['FILTER']
                    if version == '2.0.0':
                        params_no_filter['COUNT'] = str(settings.MAX_FEATURES)
                    else:
                        params_no_filter['MAXFEATURES'] = str(settings.MAX_FEATURES)

                    response = session.get(url, params=params_no_filter, timeout=settings.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        response.encoding = 'utf-8'
                        content = response.text
                    else:
                        continue

                try:
                    root = ET.fromstring(content.encode('utf-8'))

                    namespaces = {
                        'gml': 'http://www.opengis.net/gml',
                        'gml32': 'http://www.opengis.net/gml/3.2',
                        'wfs': 'http://www.opengis.net/wfs',
                        'ms': 'http://mapserver.gis.umn.edu/mapserver'
                    }

                    features = []
                    for ns_prefix in ['gml', 'gml32', 'wfs']:
                        features = root.findall(f'.//{ns_prefix}:featureMember', namespaces)
                        if features:
                            break

                    for feature_member in features:
                        if len(feature_member) > 0:
                            feature = feature_member[0]
                        else:
                            feature = feature_member

                        attributes = {}
                        geometry = None

                        for child in feature:
                            tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag

                            if any(geom_type in tag_name.lower() for geom_type in
                                   ['geom', 'polygon', 'point', 'line', 'shape']):
                                geometry = ET.tostring(child, encoding='unicode')
                            elif tag_name.lower() != 'boundedby':
                                text_value = child.text if child.text else ""
                                attributes[tag_name] = text_value

                        if entity_id in str(attributes.values()):
                            geojson_geometry = None
                            if geometry:
                                geojson_geometry = parse_gml_geometry_to_geojson(geometry)

                            return {
                                'attributes': attributes,
                                'geometry': geojson_geometry
                            }

                    if features and not any(entity_id in str(attrs) for attrs in [
                        {child.tag.split('}')[-1]: child.text for child in (f[0] if len(f) > 0 else f) if
                         not any(g in child.tag.lower() for g in ['geom', 'polygon', 'point', 'line'])}
                        for f in features[:10]
                    ]):
                        print("Sample IDs found:")
                        for i, feature_member in enumerate(features[:5]):
                            feature = feature_member[0] if len(feature_member) > 0 else feature_member
                            for child in feature:
                                tag_name = child.tag.split('}')[-1]
                                if (
                                        'id' in tag_name.lower() or 'dzial' in tag_name.lower() or 'budyn' in tag_name.lower()) and child.text:
                                    print(f"  {tag_name}: {child.text}")
                                    break

                except ET.ParseError as e:
                    print(f"XML parse error: {e}")
                    continue

        except Exception as e:
            print(f"Request error for version {version}: {e}")
            continue

    return None


def get_feature_by_id(url: str, layer_names: List[str], entity_id: str, id_field: str) -> Optional[Dict[str, Any]]:
    for layer_name in layer_names:
        try:
            result = get_feature_by_id_qgis_style(url, layer_name, entity_id, id_field)
            if result:
                return result
        except Exception as e:
            print(f"Error with layer {layer_name}: {e}")
            continue
    return None


def get_parcel_by_id(url: str, parcel_id: str) -> Optional[Dict[str, Any]]:
    return get_feature_by_id(url, settings.PARCEL_LAYER_NAMES, parcel_id, 'ID_DZIALKI')


def get_building_by_id(url: str, building_id: str) -> Optional[Dict[str, Any]]:
    return get_feature_by_id(url, settings.BUILDING_LAYER_NAMES, building_id, 'ID_BUDYNKU')
