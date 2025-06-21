class Settings:
    WFS_DATA_FILE = "data/dane_WFS.txt"
    REQUEST_TIMEOUT = 30
    MAX_FEATURES = 1000

    PARCEL_LAYER_NAMES = [
        'Dzialki', 'dzialki',
        'ms:dzialki', 'ewns:dzialki', 'wfs:dzialki',
        'ms:Dzialki', 'ewns:Dzialki', 'wfs:Dzialki'
    ]

    BUILDING_LAYER_NAMES = [
        'Budynki', 'budynki', 'budynki_wms',
        'ms:budynki', 'ewns:budynki', 'wfs:budynki',
        'ms:Budynki', 'ewns:Budynki', 'wfs:Budynki',
        'ms:budynki_wms', 'ewns:budynki_wms', 'wfs:budynki_wms',
        'blokbudynku', 'ms:blokbudynku', 'ewns:blokbudynku', 'wfs:blokbudynku'
    ]

    WFS_VERSIONS = ['1.0.0', '1.1.0', '2.0.0']


settings = Settings()