import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any

import pyproj


def detect_crs_from_gml(geometry_xml: str) -> str:
    try:
        root = ET.fromstring(geometry_xml)

        for elem in root.iter():
            srs_name = elem.get('srsName')
            if srs_name:
                if '2180' in srs_name:
                    return 'EPSG:2180'
                elif '2177' in srs_name:
                    return 'EPSG:2177'
                elif '2176' in srs_name:
                    return 'EPSG:2176'
                elif '2178' in srs_name:
                    return 'EPSG:2178'
                elif '2179' in srs_name:
                    return 'EPSG:2179'
                elif '4326' in srs_name:
                    return 'EPSG:4326'

        coord_text = ""
        for elem in root.iter():
            if elem.text and any(keyword in elem.tag for keyword in ['coordinates', 'posList', 'pos']):
                coord_text = elem.text.strip()
                break

        if coord_text:
            coords = coord_text.replace(',', ' ').split()
            if len(coords) >= 2:
                try:
                    x, y = float(coords[0]), float(coords[1])

                    if 5000000 <= x <= 7000000 and 6000000 <= y <= 7000000:
                        return 'EPSG:2180'
                    elif 100000 <= x <= 900000 and 100000 <= y <= 800000:
                        return 'EPSG:2177'
                    elif -180 <= x <= 180 and -90 <= y <= 90:
                        return 'EPSG:4326'
                except ValueError:
                    pass

    except Exception:
        pass

    return 'EPSG:2180'


def transform_coordinates_to_wgs84(coords_list: list, source_crs: str) -> list:
    if source_crs == 'EPSG:4326' or not coords_list:
        return coords_list

    print(f"Transforming {len(coords_list)} coordinates from {source_crs} to WGS84")
    print(f"Sample input coordinates: {coords_list[:2] if coords_list else 'None'}")

    try:
        transformer = pyproj.Transformer.from_crs(source_crs, 'EPSG:4326', always_xy=True)
        transformed_coords = []

        for i, coord in enumerate(coords_list):
            if len(coord) >= 2:
                x, y = coord[0], coord[1]
                try:
                    lon, lat = transformer.transform(x, y)

                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        if 10 <= lon <= 30 and 45 <= lat <= 60:
                            transformed_coords.append([lon, lat])
                            if i < 2:
                                print(f"  [{x}, {y}] -> [{lon:.6f}, {lat:.6f}]")
                        else:
                            print(f"Coordinates outside Eastern Europe, trying swapped order")
                            return transform_swapped_coordinates(coords_list, source_crs)
                    else:
                        print(f"Invalid coordinates, trying different CRS")
                        return try_different_crs(coords_list)
                except Exception as e:
                    print(f"Transform error: {e}")
                    return try_different_crs(coords_list)
            else:
                transformed_coords.append(coord)

        if transformed_coords:
            print(f"Successfully transformed to: {transformed_coords[:2] if transformed_coords else 'None'}")
            return transformed_coords
        else:
            return try_different_crs(coords_list)

    except Exception as e:
        print(f"Transformation failed: {e}")
        return try_different_crs(coords_list)


def transform_swapped_coordinates(coords_list: list, source_crs: str) -> list:
    try:
        transformer = pyproj.Transformer.from_crs(source_crs, 'EPSG:4326', always_xy=True)
        transformed_coords = []

        for coord in coords_list:
            if len(coord) >= 2:
                y, x = coord[0], coord[1]  # Swapped order
                try:
                    lon, lat = transformer.transform(x, y)

                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        if 10 <= lon <= 30 and 45 <= lat <= 60:
                            transformed_coords.append([lon, lat])
                        else:
                            return coords_list
                    else:
                        return coords_list
                except Exception:
                    return coords_list
            else:
                transformed_coords.append(coord)

        if transformed_coords:
            print(f"Successfully transformed with swapped coordinates")
            return transformed_coords
        else:
            return coords_list

    except Exception:
        return coords_list


def try_different_crs(coords_list: list) -> list:
    polish_systems = ['EPSG:2180', 'EPSG:2177', 'EPSG:2176', 'EPSG:2178', 'EPSG:2179']

    for crs in polish_systems:
        try:
            transformer = pyproj.Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)

            if coords_list:
                test_coord = coords_list[0]
                if len(test_coord) >= 2:
                    x, y = test_coord[0], test_coord[1]
                    lon, lat = transformer.transform(x, y)

                    if 14 <= lon <= 24 and 49 <= lat <= 54:
                        print(f"Found correct CRS: {crs}")
                        return transform_coordinates_to_wgs84(coords_list, crs)

                    y, x = test_coord[0], test_coord[1]  # Try swapped
                    lon, lat = transformer.transform(x, y)

                    if 14 <= lon <= 24 and 49 <= lat <= 54:
                        print(f"Found correct CRS with swapped coordinates: {crs}")
                        return transform_swapped_coordinates(coords_list, crs)

        except Exception:
            continue

    print("Could not find suitable transformation, returning original coordinates")
    return coords_list


def parse_gml_geometry_to_geojson(geometry_xml: str) -> Optional[Dict[str, Any]]:
    if not geometry_xml or not geometry_xml.strip():
        return None

    try:
        root = ET.fromstring(geometry_xml)
        source_crs = detect_crs_from_gml(geometry_xml)
        print(f"Detected CRS: {source_crs}")

        def extract_coordinates(coord_text: str) -> list:
            coords = []
            coord_text = coord_text.strip()

            if ',' in coord_text:
                coord_pairs = coord_text.split()
                for pair in coord_pairs:
                    if ',' in pair:
                        parts = pair.split(',')
                        if len(parts) >= 2:
                            try:
                                x = float(parts[0])
                                y = float(parts[1])
                                coords.append([x, y])
                            except ValueError:
                                continue
            else:
                coord_pairs = coord_text.split()
                for i in range(0, len(coord_pairs), 2):
                    if i + 1 < len(coord_pairs):
                        try:
                            x = float(coord_pairs[i])
                            y = float(coord_pairs[i + 1])
                            coords.append([x, y])
                        except ValueError:
                            continue
            return coords

        for child in root.iter():
            if 'Polygon' in child.tag:
                exterior_coords = []
                interior_coords = []

                for subchild in child.iter():
                    if 'exterior' in subchild.tag or 'outerBoundaryIs' in subchild.tag:
                        for coord_elem in subchild.iter():
                            if coord_elem.text and any(
                                    keyword in coord_elem.tag for keyword in ['coordinates', 'posList']):
                                exterior_coords = extract_coordinates(coord_elem.text)
                    elif 'interior' in subchild.tag or 'innerBoundaryIs' in subchild.tag:
                        for coord_elem in subchild.iter():
                            if coord_elem.text and any(
                                    keyword in coord_elem.tag for keyword in ['coordinates', 'posList']):
                                interior_coords.append(extract_coordinates(coord_elem.text))

                if exterior_coords:
                    print(f"Original exterior coordinates: {exterior_coords[:2] if exterior_coords else 'None'}")

                    transformed_exterior = transform_coordinates_to_wgs84(exterior_coords, source_crs)

                    coordinates = [transformed_exterior]

                    if interior_coords:
                        transformed_interior = []
                        for interior in interior_coords:
                            transformed_interior.append(transform_coordinates_to_wgs84(interior, source_crs))
                        coordinates.extend(transformed_interior)

                    return {
                        "type": "Polygon",
                        "coordinates": coordinates
                    }

            elif 'Point' in child.tag:
                for coord_elem in child.iter():
                    if coord_elem.text and any(keyword in coord_elem.tag for keyword in ['coordinates', 'pos']):
                        coord_text = coord_elem.text.strip()
                        coords = None

                        if ',' in coord_text:
                            parts = coord_text.split(',')
                            if len(parts) >= 2:
                                coords = [[float(parts[0]), float(parts[1])]]
                        else:
                            coords_list = coord_text.split()
                            if len(coords_list) >= 2:
                                coords = [[float(coords_list[0]), float(coords_list[1])]]

                        if coords:
                            transformed_coords = transform_coordinates_to_wgs84(coords, source_crs)
                            return {
                                "type": "Point",
                                "coordinates": transformed_coords[0] if transformed_coords else coords[0]
                            }

            elif 'LineString' in child.tag or 'Line' in child.tag:
                for coord_elem in child.iter():
                    if coord_elem.text and any(keyword in coord_elem.tag for keyword in ['coordinates', 'posList']):
                        coords = extract_coordinates(coord_elem.text)
                        if coords:
                            transformed_coords = transform_coordinates_to_wgs84(coords, source_crs)
                            return {
                                "type": "LineString",
                                "coordinates": transformed_coords if transformed_coords else coords
                            }

    except Exception as e:
        print(f"Error parsing geometry: {e}")

    return None
