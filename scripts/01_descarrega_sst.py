"""Descarrega totes les dades d'entrada del projecte a datasets/.

1. Límits de les GSA (GFCM/FAO) -> datasets/gsa_med.geojson
   La FAO no ofereix una descàrrega directa estable; el paquet R RoME inclou el shapefile de
   les GSA de la GFCM com a objecte R (MedSea), que es llegeix amb `rdata` sense necessitat de R.
2. Terra (Natural Earth 1:50m), retallada al Mediterrani -> datasets/terra_med.geojson
3. Temperatura superficial mensual (Copernicus Marine) -> datasets/copernicus/med_sst_mensual.nc
   Producte: MEDSEA_MULTIYEAR_PHY_006_004 (reanàlisi física, 1/24°, mensual, 1987-2026)
   Dataset:  cmems_mod_med_phy-temp_my_4.2km_P1M-m, variable thetao a ~1 m (superfície)
   Requisit: compte gratuït a https://data.marine.copernicus.eu i `copernicusmarine login`.
"""
import urllib.request
import warnings
from pathlib import Path

import copernicusmarine
import geopandas as gpd
import rdata
from shapely.geometry import MultiPolygon, Polygon, box

DATASETS = Path(__file__).resolve().parent.parent / "datasets"

URL_GSA = "https://raw.githubusercontent.com/COISPA/RoME/master/data/MedSea.rda"
URL_TERRA = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson"

# --- 1. Límits de les GSA ----------------------------------------------------
rda = DATASETS / "gsa_raw" / "MedSea.rda"
rda.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(URL_GSA, rda)

with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)  # rdata avisa que no coneix les classes de R (sp)
    med_sea = rdata.read_rda(rda)["MedSea"]       # SpatialPolygonsDataFrame: una entrada per GSA

# Cada GSA és una llista d'anells; només es conserven els exteriors (els forats són illes)
geometries = [
    MultiPolygon([Polygon(anell.coords) for anell in gsa.Polygons if not anell.hole[0]])
    for gsa in med_sea.polygons
]
gsa = gpd.GeoDataFrame({"GSA": med_sea.data["NOME_GSA"].astype(int)}, geometry=geometries, crs="EPSG:4326")
gsa.sort_values("GSA").to_file(DATASETS / "gsa_med.geojson", driver="GeoJSON")
print("->", DATASETS / "gsa_med.geojson")

# --- 2. Terra -----------------------------------------------------------------
terra = gpd.read_file(URL_TERRA).clip(box(-8, 28, 38, 48))
terra[["geometry"]].to_file(DATASETS / "terra_med.geojson", driver="GeoJSON")
print("->", DATASETS / "terra_med.geojson")

# --- 3. Temperatura superficial (Copernicus Marine) --------------------------
copernicusmarine.subset(
    dataset_id="cmems_mod_med_phy-temp_my_4.2km_P1M-m",
    variables=["thetao"],
    minimum_longitude=-6.0,
    maximum_longitude=36.5,
    minimum_latitude=30.0,
    maximum_latitude=46.0,
    minimum_depth=0.0,
    maximum_depth=1.1,  # només la primera capa (~1 m) = superfície
    output_directory=str(DATASETS / "copernicus"),
    output_filename="med_sst_mensual.nc",
    overwrite=True,
)
