import csv
from typing import Optional, Dict


def get_teryt_from_id(entity_id: str) -> str:
    return entity_id[:4]


def find_service_by_teryt(file_path: str, teryt: str) -> Optional[Dict[str, str]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            next(f)
            csv_reader = csv.reader(f, delimiter=';')
            for row in csv_reader:
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
