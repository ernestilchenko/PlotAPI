from typing import Optional, Dict

import aiofiles


def get_teryt_from_id(entity_id: str) -> str:
    return entity_id[:4]


async def find_service_by_teryt(file_path: str, teryt: str) -> Optional[Dict[str, str]]:
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            await f.readline()
            content = await f.read()

        lines = content.strip().split('\n')
        for line in lines:
            row = line.split(';')
            if len(row) >= 4 and row[2] == teryt:
                return {
                    'id': row[0],
                    'organization': row[1],
                    'teryt': row[2],
                    'url': row[3]
                }
    except FileNotFoundError:
        return None
    return None
