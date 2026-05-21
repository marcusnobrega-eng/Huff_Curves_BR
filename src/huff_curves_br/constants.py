"""Project constants and Huff reference curves."""

import numpy as np

ANA_ENDPOINT = (
    "https://telemetriaws1.ana.gov.br/ServiceANA.asmx/"
    "DadosHidrometeorologicos"
)

IBGE_MALHAS_API = "https://servicodados.ibge.gov.br/api/v3/malhas"
IBGE_LOCALIDADES_API = "https://servicodados.ibge.gov.br/api/v1/localidades"
IBGE_BIOMES_2025_ZIP_URL = (
    "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
    "biomas/vetores/2025_Biomas-e-Sistema-Costeiro-Marinho-do-Brasil-1-250000_shp.zip"
)

DEFAULT_START_DATE = "2014-01-01"
DEFAULT_END_DATE = "2024-12-31"

DEFAULT_IETD_HOURS = 6.0
DEFAULT_MIN_EVENT_DEPTH_MM = 1.0
DEFAULT_MIN_EVENT_RECORDS = 4
DEFAULT_MAX_EVENT_DURATION_HOURS = 96.0
DEFAULT_MAX_INTENSITY_MM_H = 300.0
DEFAULT_MAX_MISSING_FRACTION = 0.20
DEFAULT_MIN_YEARS = 4.0
DEFAULT_FIXED_DAY_START_HOUR = 7
DEFAULT_DAILY_MIN_DEPTH_MM = 0.2

HUFF_REFERENCE_TAU = np.round(np.arange(0.1, 1.01, 0.1), 10)

# Polynomial coefficients for the original Huff reference curves.
# Rows are quartiles 1..4; coefficients are ordered for numpy.polyval.
HUFF_REFERENCE_COEFFICIENTS = np.array(
    [
        [-0.9633, 3.8869, -7.8950, 10.0890, -8.0108, 3.8936, -0.0032],
        [-39.4360, 125.1800, -146.0400, 73.6040, -13.9360, 1.6243, -0.0068],
        [46.5420, -131.5500, 132.6300, -57.3150, 10.7960, -0.1107, 0.0050],
        [-25.2890, 67.5400, -64.9260, 28.0310, -5.2061, 0.8535, -0.0042],
    ],
    dtype=float,
)

HUFF_FIT_DEGREE = 7
HUFF_PERCENTILE_LEVELS = tuple(range(10, 100, 10))
HUFF_INTERP_STEP = 0.02
