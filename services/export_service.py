import asyncio
import io
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape


async def create_geodataframe(data: Dict[str, Any], entity_id: str, entity_type: str) -> gpd.GeoDataFrame:
    def _create_gdf():
        attributes = data['attributes'].copy()
        attributes['entity_id'] = entity_id
        attributes['entity_type'] = entity_type
        attributes['author'] = 'ernestilchenko'

        geometry = None
        if data['geometry']:
            geometry = shape(data['geometry'])

        df_data = {k: [v] for k, v in attributes.items()}
        df = pd.DataFrame(df_data)

        if geometry:
            gdf = gpd.GeoDataFrame(df, geometry=[geometry], crs='EPSG:4326')
        else:
            gdf = gpd.GeoDataFrame(df)

        return gdf

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _create_gdf)


async def export_to_geojson(gdf: gpd.GeoDataFrame) -> str:
    def _export():
        return gdf.to_json()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _export)


async def export_to_gml(gdf: gpd.GeoDataFrame) -> bytes:
    def _export():
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "export.gml")
            gdf.to_file(temp_file, driver="GML")
            with open(temp_file, 'rb') as f:
                return f.read()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _export)


async def export_to_kml(gdf: gpd.GeoDataFrame) -> bytes:
    def _export():
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "export.kml")
            gdf.to_file(temp_file, driver="KML")
            with open(temp_file, 'rb') as f:
                return f.read()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _export)


async def export_to_shapefile(gdf: gpd.GeoDataFrame) -> bytes:
    def _export():
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "export.shp")
            gdf.to_file(temp_file)

            buffer = io.BytesIO()
            import zipfile

            with zipfile.ZipFile(buffer, 'w') as zf:
                base_name = Path(temp_file).stem
                extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']

                for ext in extensions:
                    file_path = os.path.join(temp_dir, f"{base_name}{ext}")
                    if os.path.exists(file_path):
                        zf.write(file_path, f"{base_name}{ext}")

            buffer.seek(0)
            return buffer.read()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _export)


async def get_export_data(data: Dict[str, Any], entity_id: str, entity_type: str, format_type: str) -> tuple[
    bytes, str, str]:
    gdf = await create_geodataframe(data, entity_id, entity_type)

    if format_type.lower() == 'geojson':
        content_str = await export_to_geojson(gdf)
        content = content_str.encode('utf-8')
        media_type = "application/geo+json"
        filename = f"{entity_id}_by_ernestilchenko.geojson"
    elif format_type.lower() == 'gml':
        content = await export_to_gml(gdf)
        media_type = "application/gml+xml"
        filename = f"{entity_id}_by_ernestilchenko.gml"
    elif format_type.lower() == 'kml':
        content = await export_to_kml(gdf)
        media_type = "application/vnd.google-earth.kml+xml"
        filename = f"{entity_id}_by_ernestilchenko.kml"
    elif format_type.lower() == 'shp':
        content = await export_to_shapefile(gdf)
        media_type = "application/zip"
        filename = f"{entity_id}_shapefile_by_ernestilchenko.zip"
    else:
        raise ValueError(f"Unsupported format: {format_type}")

    return content, media_type, filename
