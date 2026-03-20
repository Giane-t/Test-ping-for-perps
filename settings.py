from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"

PING_COUNT = 4
PING_TIMEOUT_SECONDS = 3
PING_COMMAND_TIMEOUT_SECONDS = 30
HTTP_TIMEOUT_SECONDS = 10
GEOIP_TIMEOUT_SECONDS = 10
GEOIP_PAUSE_SECONDS = 0.5

GEOIP_API = (
    "http://ip-api.com/json/{ip}"
    "?fields=status,message,country,countryCode,region,regionName,city,lat,lon,isp,org,as,query"
)

EXCHANGES = {
    "Hibachi": {
        "endpoints": [
            "https://api-doc.hibachi.xyz/",
            "https://hibachi.xyz/",
        ],
        "description": "Decentralized derivatives trading protocol",
    },
    "Nado": {
        "endpoints": [
            "https://gateway.prod.nado.xyz/v1",
            "https://archive.prod.nado.xyz/v1",
            "https://trigger.prod.nado.xyz/v1",
        ],
        "description": "CLOB DEX on Ink L2 (Kraken)",
    },
    "Lighter": {
        "endpoints": [
            "https://mainnet.zklighter.elliot.ai/",
            "https://apidocs.lighter.xyz/",
        ],
        "description": "ZK-rollup perpetual futures DEX",
    },
    "Variational": {
        "endpoints": [
            "https://omni-client-api.prod.ap-northeast-1.variational.io/",
            "https://omni.variational.io/",
        ],
        "description": "P2P derivatives protocol (Omni)",
    },
    "Extended": {
        "endpoints": [
            "https://api.starknet.extended.exchange/",
            "https://app.extended.exchange/",
        ],
        "description": "Hybrid perpetuals exchange on Starknet",
    },
}
