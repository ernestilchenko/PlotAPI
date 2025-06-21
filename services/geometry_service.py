import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any


def parse_gml_geometry_to_geojson(geometry_xml: str) -> Optional[Dict[str, Any]]:
    try:
        root = ET.fromstring(geometry_xml)

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
                    coordinates = [exterior_coords]
                    if interior_coords:
                        coordinates.extend(interior_coords)

                    return {
                        "type": "Polygon",
                        "coordinates": coordinates
                    }

            elif 'Point' in child.tag:
                for coord_elem in child.iter():
                    if coord_elem.text and any(keyword in coord_elem.tag for keyword in ['coordinates', 'pos']):
                        coord_text = coord_elem.text.strip()
                        if ',' in coord_text:
                            parts = coord_text.split(',')
                            if len(parts) >= 2:
                                return {
                                    "type": "Point",
                                    "coordinates": [float(parts[0]), float(parts[1])]
                                }
                        else:
                            coords = coord_text.split()
                            if len(coords) >= 2:
                                return {
                                    "type": "Point",
                                    "coordinates": [float(coords[0]), float(coords[1])]
                                }

            elif 'LineString' in child.tag or 'Line' in child.tag:
                for coord_elem in child.iter():
                    if coord_elem.text and any(keyword in coord_elem.tag for keyword in ['coordinates', 'posList']):
                        coords = extract_coordinates(coord_elem.text)
                        if coords:
                            return {
                                "type": "LineString",
                                "coordinates": coords
                            }

    except Exception as e:
        print(f"Error parsing geometry: {e}")
        pass

    return None
