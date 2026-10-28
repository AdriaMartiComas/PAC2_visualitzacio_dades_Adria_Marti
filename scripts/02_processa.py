"""Agrega la SST mensual per GSA i prepara les taules per a les tres visualitzacions.

Sortides (datasets/processat/):
  - sst_mensual_gsa.csv     : GSA, data, sst (mitjana espacial mensual)  -> box plot
  - resum_gsa.csv           : GSA, mitjana, tendència °C/dècada, anomalia -> choropleth
  - sst_clim_estiu.nc       : camp mitjà d'agost (graella)                -> contour plot
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import regionmask
import xarray as xr

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "datasets" / "copernicus"
OUT = ROOT / "datasets" / "processat"
OUT.mkdir(parents=True, exist_ok=True)

# --- Dades SST -------------------------------------------------------------
ds = xr.open_dataset(RAW / "med_sst_mensual.nc")
sst = ds["thetao"].isel(depth=0).drop_vars("depth")

# Només anys complets
mesos_per_any = sst["time"].dt.year.to_series().value_counts()
anys_complets = mesos_per_any[mesos_per_any == 12].index
sst = sst.sel(time=sst["time"].dt.year.isin(anys_complets)).load()

# --- GSA -------------------------------------------------------------------
gsa = gpd.read_file(ROOT / "datasets" / "gsa_med.geojson")
gsa = gsa[gsa["GSA"] <= 28]  # 29-30 = mar Negre i d'Azov, fora del domini
regions = regionmask.from_geopandas(gsa, numbers="GSA", names="GSA", overlap=False)
mascara = regions.mask(sst["longitude"], sst["latitude"])

# Pes per àrea de cel·la (cos lat)
pesos = np.cos(np.deg2rad(sst["latitude"]))

files = []
for n in gsa["GSA"]:
    serie = sst.where(mascara == n).weighted(pesos).mean(["latitude", "longitude"])
    if serie.isnull().all():
        continue
    files.append(pd.DataFrame({"GSA": n, "data": serie["time"].values, "sst": serie.values}))
mensual = pd.concat(files).dropna()
mensual.to_csv(OUT / "sst_mensual_gsa.csv", index=False)

# --- Resum per GSA (choropleth) --------------------------------------------
mensual["any"] = pd.to_datetime(mensual["data"]).dt.year
anual = mensual.groupby(["GSA", "any"])["sst"].mean().reset_index()
ref = anual[anual["any"].between(1991, 2020)].groupby("GSA")["sst"].mean()
ultim_any = anual["any"].max()


def tendencia(df):
    pendent = np.polyfit(df["any"], df["sst"], 1)[0]
    return pendent * 10  # °C per dècada


resum = pd.DataFrame({
    "sst_mitjana": anual.groupby("GSA")["sst"].mean(),
    "tendencia_decada": anual.groupby("GSA").apply(tendencia, include_groups=False),
    "anomalia_ultim_any": anual[anual["any"] == ultim_any].set_index("GSA")["sst"] - ref,
}).round(3).reset_index()
resum["ultim_any"] = ultim_any
resum.to_csv(OUT / "resum_gsa.csv", index=False)

# --- Camps per al contour plot ----------------------------------------------
agost = sst.sel(time=sst["time"].dt.month == 8).mean("time")
agost = agost.coarsen(latitude=3, longitude=3, boundary="trim").mean()  # ~12 km, prou per isotermes
agost.to_netcdf(OUT / "sst_clim_estiu.nc")

print(resum.sort_values("tendencia_decada", ascending=False).to_string(index=False))
