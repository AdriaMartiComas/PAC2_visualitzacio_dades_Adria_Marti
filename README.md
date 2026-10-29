# PAC 2 – Temperatura del Mediterrani per GSA

Autor: Adrià Martí Comas

## Grafics publics

-<https://adriamarticomas.github.io/PAC2_visualitzacio_dades_Adria_Marti/choropleth.html>
-<https://adriamarticomas.github.io/PAC2_visualitzacio_dades_Adria_Marti/boxplot.html>
-<https://adriamarticomas.github.io/PAC2_visualitzacio_dades_Adria_Marti/contour.html>

## Passos per generar els gràfics

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/copernicusmarine login                 # un cop, amb el compte gratuït de Copernicus Marine
.venv/bin/python scripts/01_descarrega_sst.py    # baixa GSA, terra i temperatura -> datasets/
.venv/bin/python scripts/02_processa.py          # taules per GSA -> datasets/processat/
.venv/bin/python scripts/03_visualitzacions.py   # gràfics -> docs/*.html
```

Executa els scripts des de l'arrel del projecte i en aquest ordre: cadascun fa servir el que genera l'anterior.

Tècniques: **Choropleth map**, **Box plot**, **Contour plot**.

Dades (totes les baixa `01_descarrega_sst.py`):

- SST: Copernicus Marine, `MEDSEA_MULTIYEAR_PHY_006_004` (reanàlisi, mensual, 1/24°, 1987–2026), variable `thetao` a ~1 m. Requereix compte gratuït.
- Límits: Geographical Sub-Areas (GSA) de la GFCM/FAO. S'obtenen de l'objecte `MedSea` del paquet R [RoME](https://github.com/COISPA/RoME), llegit amb `rdata` (no cal tenir R instal·lat).
- Terra (contour): Natural Earth 1:50m `ne_50m_land`, retallada al Mediterrani.
