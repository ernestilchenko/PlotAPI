class Settings:
    WFS_DATA_FILE = "data/dane_WFS.txt"
    REQUEST_TIMEOUT = 30
    MAX_FEATURES = 1000

    PARCEL_LAYER_NAMES = [
        'ewns:dzialki',
        'dzialki',
        'ms:dzialki',
        'wfs:dzialki'
    ]

    BUILDING_LAYER_NAMES = [
        'ewns:budynki',
        'budynki',
        'budynki_wms',
        'ms:budynki',
        'wfs:budynki',
        'ms:budynki_wms',
        'blokbudynku',
        'ms:blokbudynku'
    ]

    PARCEL_ID_FIELD = 'idDzialki'
    BUILDING_ID_FIELD = 'idBudynku'

    FALLBACK_PARCEL_ID_FIELDS = ['ID_DZIALKI', 'id_dzialki', 'idDzialki', 'IDDZ']
    FALLBACK_BUILDING_ID_FIELDS = ['ID_BUDYNKU', 'id_budynku', 'idBudynku', 'IDBU']

    WFS_VERSIONS = ['2.0.0', '1.1.0', '1.0.0']


settings = Settings()