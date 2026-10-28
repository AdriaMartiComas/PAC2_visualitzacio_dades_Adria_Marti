"""Genera les tres visualitzacions interactives (Plotly) a docs/ per publicar-les a GitHub Pages.

  docs/choropleth.html  -> tendència d'escalfament per GSA
  docs/boxplot.html     -> distribució de la SST mensual per GSA
  docs/contour.html     -> isotermes de la SST mitjana d'agost
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import xarray as xr

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "datasets" / "processat"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

FONT = "Inter, system-ui, sans-serif"
SUPERFICIE = "#fcfcfb"
TEXT, TEXT2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLAU = "#2a78d6"
# Rampa seqüencial d'un sol to (taronja), clar -> fosc
TARONJA = [[0, "#fde6d8"], [0.25, "#f6b48f"], [0.5, "#eb6834"], [0.75, "#b8461c"], [1, "#6e2a10"]]
FONT_DADES = "Font: Copernicus Marine Service, MEDSEA_MULTIYEAR_PHY_006_004 · GSA: GFCM (FAO)"

NOMS_GSA = {
    1: "Mar d'Alborán nord", 2: "Illa d'Alborán", 3: "Mar d'Alborán sud", 4: "Algèria",
    5: "Illes Balears", 6: "Nord de la península Ibèrica", 7: "Golf de Lleó", 8: "Còrsega",
    9: "Mar Lígur i Tirrè nord", 10: "Tirrè sud i central", 11: "Sardenya", 12: "Tunísia nord",
    13: "Golf d'Hammamet", 14: "Golf de Gabès", 15: "Malta", 16: "Sud de Sicília",
    17: "Adriàtic nord", 18: "Adriàtic sud", 19: "Jònic occidental", 20: "Jònic oriental",
    21: "Jònic sud", 22: "Mar Egea", 23: "Creta", 24: "Llevant nord", 25: "Xipre",
    26: "Llevant sud", 27: "Llevant", 28: "Mar de Màrmara",
}


def estil(fig, titol, subtitol):
    fig.update_layout(
        title=dict(text=f"<b>{titol}</b><br><span style='font-size:13px;color:{TEXT2}'>{subtitol}</span>",
                   x=0.02, xanchor="left"),
        font=dict(family=FONT, color=TEXT, size=13),
        paper_bgcolor=SUPERFICIE, plot_bgcolor=SUPERFICIE,
        margin=dict(l=60, r=30, t=90, b=110), height=650,
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=TEXT)),
    )
    fig.add_annotation(text=FONT_DADES, xref="paper", yref="paper", x=0, y=0, yshift=-80,
                       yanchor="top", showarrow=False, font=dict(size=11, color=TEXT2), xanchor="left")
    return fig


def desa(fig, nom):
    fig.write_html(DOCS / nom, include_plotlyjs="cdn", full_html=True,
                   config={"displaylogo": False, "responsive": True})
    print("->", DOCS / nom)


gsa = gpd.read_file(ROOT / "datasets" / "gsa_med.geojson")
gsa = gsa[gsa["GSA"] <= 28].copy()
gsa["geometry"] = gsa.geometry.simplify(0.02, preserve_topology=True)  # fitxer HTML lleuger
gsa["nom"] = gsa["GSA"].map(NOMS_GSA)
ordre_oest_est = gsa.assign(x=gsa.geometry.representative_point().x).sort_values("x")["GSA"].tolist()

resum = pd.read_csv(PROC / "resum_gsa.csv")
mensual = pd.read_csv(PROC / "sst_mensual_gsa.csv", parse_dates=["data"])
anys = f"{mensual['data'].dt.year.min()}–{mensual['data'].dt.year.max()}"

# --- 1. Choropleth -----------------------------------------------------------
df = gsa[["GSA", "nom"]].merge(resum, on="GSA")
fig = go.Figure(go.Choropleth(
    geojson=gsa.set_index("GSA").__geo_interface__,
    locations=df["GSA"].astype(str), z=df["tendencia_decada"],
    featureidkey="id", colorscale=TARONJA,
    marker_line_color="white", marker_line_width=1,
    colorbar=dict(title="°C / dècada", thickness=12, outlinewidth=0),
    customdata=df[["nom", "sst_mitjana", "anomalia_ultim_any"]],
    hovertemplate=("<b>GSA %{location} · %{customdata[0]}</b><br>"
                   "Tendència: <b>%{z:+.2f} °C/dècada</b><br>"
                   "SST mitjana: %{customdata[1]:.1f} °C<br>"
                   f"Anomalia {int(resum['ultim_any'].iloc[0])} vs 1991–2020: "
                   "%{customdata[2]:+.2f} °C<extra></extra>"),
))
fig.update_geos(lonaxis_range=[-6, 37], lataxis_range=[30, 46.5], visible=False, showland=True, landcolor="#e9e8e4",
                showcoastlines=True, coastlinecolor="#c3c2b7", bgcolor=SUPERFICIE,
                projection_type="mercator", domain=dict(x=[0, 0.92], y=[0, 1]))
estil(fig, "On s'escalfa més ràpid el Mediterrani?",
      f"Tendència lineal de la temperatura superficial del mar per subàrea geogràfica (GSA), {anys}")
fig.update_layout(margin=dict(l=20, r=20, b=60))
fig.layout.annotations[0].update(yshift=-20)
desa(fig, "choropleth.html")

# --- 2. Box plot -------------------------------------------------------------
fig = go.Figure()
filtres = {"Tots els mesos": mensual, "Agost": mensual[mensual["data"].dt.month == 8],
           "Febrer": mensual[mensual["data"].dt.month == 2]}
for i, (etiqueta, d) in enumerate(filtres.items()):
    fig.add_trace(go.Box(
        x=d["GSA"].astype(str), y=d["sst"], name=etiqueta, visible=(i == 0),
        marker=dict(color=BLAU, size=4), line=dict(width=1.5), fillcolor="rgba(42,120,214,0.18)",
        boxpoints="outliers",
        hovertemplate="GSA %{x}<br>%{y:.1f} °C<extra></extra>",
    ))
fig.update_layout(
    showlegend=False,
    updatemenus=[dict(type="buttons", direction="right", x=1, y=1.02, xanchor="right", yanchor="bottom",
                      bgcolor="white", bordercolor=GRID, font=dict(size=12),
                      buttons=[dict(label=k, method="update",
                                    args=[{"visible": [j == i for j in range(len(filtres))]}])
                               for i, k in enumerate(filtres)])],
)
fig.update_xaxes(title="GSA (ordenades d'oest a est)", categoryorder="array",
                 categoryarray=[str(g) for g in ordre_oest_est if g in set(mensual["GSA"])],
                 showgrid=False, linecolor=GRID)
fig.update_yaxes(title="Temperatura superficial (°C)", gridcolor=GRID, zeroline=False)
estil(fig, "Com varia la temperatura del mar a cada GSA?",
      f"Distribució de la SST mitjana mensual per subàrea, {anys}")
desa(fig, "boxplot.html")

# --- 3. Contour plot ---------------------------------------------------------
agost = xr.open_dataarray(PROC / "sst_clim_estiu.nc")
fig = go.Figure(go.Contour(
    x=agost["longitude"].values, y=agost["latitude"].values, z=agost.values,
    colorscale=TARONJA, contours=dict(start=20, end=29, size=1, showlabels=True,
                                      labelfont=dict(size=10, color="white")),
    line=dict(width=0.8, color="rgba(255,255,255,0.6)"),
    colorbar=dict(title="°C", thickness=12, outlinewidth=0),
    hovertemplate="%{x:.2f}° E, %{y:.2f}° N<br>%{z:.1f} °C<extra></extra>",
    connectgaps=False,
))
# Terra en gris, com al choropleth (Natural Earth 1:50m), dibuixada com a formes per sobre del contour
terra = gpd.read_file(ROOT / "datasets" / "terra_med.geojson")
for geom in terra.geometry:
    for poligon in getattr(geom, "geoms", [geom]):
        path = " ".join(
            "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in anell.coords) + " Z"
            for anell in [poligon.exterior, *poligon.interiors])
        fig.add_shape(type="path", path=path, fillcolor="#e9e8e4", fillrule="evenodd",
                      line=dict(color="#c3c2b7", width=0.6), layer="above")
# Límits de les GSA superposats per lligar-ho amb el choropleth
for geom in gsa.geometry.boundary:
    for linia in getattr(geom, "geoms", [geom]):
        xs, ys = linia.xy
        fig.add_trace(go.Scatter(x=list(xs), y=list(ys), mode="lines", hoverinfo="skip",
                                 line=dict(color="rgba(11,11,11,0.35)", width=0.7), showlegend=False))
for _, r in gsa[gsa["GSA"].isin(resum["GSA"])].iterrows():
    c = r.geometry.representative_point()
    fig.add_trace(go.Scatter(x=[c.x], y=[c.y], mode="text", text=[str(r["GSA"])], hoverinfo="skip",
                             textfont=dict(size=10, color=TEXT2), showlegend=False))
fig.update_xaxes(title="Longitud (°E)", range=[-6, 36.5], showgrid=False, zeroline=False)
fig.update_yaxes(title="Latitud (°N)", range=[30, 46], showgrid=False, zeroline=False,
                 scaleanchor="x", scaleratio=1.3)
estil(fig, "Isotermes del Mediterrani a l'agost",
      f"Temperatura superficial mitjana del mes d'agost, {anys}. Línies cada 1 °C; números = GSA")
desa(fig, "contour.html")
