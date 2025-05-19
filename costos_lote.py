"""
Streamlit app — Calculadora de costo de producción (cerveza artesanal)
Versión 2.2  🇦🇷
• Preset realista 20 L (botellas 330 ml).
• Descarga y carga de CSV completa.
• **Subtítulos descriptivos** restaurados en cada sección con breve explicación.
"""

import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Costo de Producción de Cerveza", page_icon="💸", layout="wide")

UNITS = ["kg", "g", "L", "ml"]

# ---------------------------------------------------------------------------
# Defaults (preset 20 L) ------------------------------------------------------
# ---------------------------------------------------------------------------

def default_ingredients():
    descr = [
        "Agua", "Malta Pilsen", "Malta caramelo", "Lúpulo", "Levadura ale"
    ]
    qty   = [25.0, 4.5, 0.3, 0.05, 0.011]
    unit  = ["L", "kg", "kg", "kg", "kg"]
    price = [2, 550, 820, 16000, 12500]
    while len(descr) < 10:
        descr.append(""); qty.append(0.0); unit.append("kg"); price.append(0)
    return pd.DataFrame({"Descripción": descr, "Cantidad": qty, "Unidad": unit, "Costo unitario (ARS $)": price})


def default_packaging():
    return pd.DataFrame({
        "Descripción": ["Botella 330 ml", "Chapa", "Etiqueta", "Cartón 6 pack"],
        "Unidades": [61, 61, 61, 11],
        "Costo unitario (ARS $)": [80, 15, 20, 300]
    })


def default_aux():
    return pd.DataFrame({
        "Descripción": ["CO₂", "Irish moss"],
        "Cantidad": [0.6, 5],
        "Unidad": ["kg", "g"],
        "Costo unitario (ARS $)": [700, 80]
    })

# ---------------------------------------------------------------------------
# CSV helpers ----------------------------------------------------------------
# ---------------------------------------------------------------------------

def build_save_df(params: dict, ing_df, pack_df, aux_df):
    rows = [{"Section": "PARAM", "Field": k, "Value": v} for k, v in params.items()]
    rows += [
        {"Section": "Ingredientes", "Field": "Data", "Value": ing_df.to_json(orient="records")},
        {"Section": "Packaging", "Field": "Data", "Value": pack_df.to_json(orient="records")},
        {"Section": "Auxiliares", "Field": "Data", "Value": aux_df.to_json(orient="records")},
    ]
    return pd.DataFrame(rows)


def load_save_df(df):
    params, tables = {}, {}
    for _, row in df.iterrows():
        if row["Section"] == "PARAM":
            params[row["Field"]] = row["Value"]
        else:
            tables[row["Section"]] = pd.read_json(row["Value"], orient="records")
    return params, tables

# ---------------------------------------------------------------------------
# Sidebar upload -------------------------------------------------------------
# ---------------------------------------------------------------------------

st.sidebar.header("📂 Cargar CSV guardado")
file_up = st.sidebar.file_uploader("Selecciona archivo CSV", type="csv")
loaded_params, loaded_tables = {}, {}
if file_up is not None:
    try:
        df_saved = pd.read_csv(file_up)
        loaded_params, loaded_tables = load_save_df(df_saved)
        st.sidebar.success("Archivo cargado correctamente")
    except Exception as e:
        st.sidebar.error(f"Error al leer CSV: {e}")

# ---------------------------------------------------------------------------
# Encabezado -----------------------------------------------------------------
# ---------------------------------------------------------------------------

# ---- Título del lote --------------------------------------------------------
lot_title_default = loaded_params.get("Titulo_lote", "Lote 20 L")
st.markdown("""<div style='text-align:center;font-size:1.1rem;'>
<a href='https://www.nosoynormalcerveceria.com' target='_blank'>Mirá más calculadoras para productores de bebidas en www.nosoynormalcerveceria.com</a>
</div>""", unsafe_allow_html=True)
lot_title = st.text_input("Título del lote", lot_title_default)

st.title(f"Costo de producción — {lot_title}")

def p(name, default):
    return float(loaded_params.get(name, default))

col1, col2, col3 = st.columns(3)
vol_batch = col1.number_input("Volumen del lote (L)", 1.0, 2000.0, p("Volumen_L", 20.0))

bottle_ml = col2.number_input("Tamaño botella/lata (ml)", 250, 1000, int(p("Bottle_ml", 330)), step=10)

loss_pct = col3.number_input("% Perdido", 0.0, 25.0, p("Merma_pct", 8.0), step=0.5, help="Volumen que se pierde por trub, purgas y roturas.")

# ---------------------------------------------------------------------------
# 1. Ingredientes ------------------------------------------------------------
# ---------------------------------------------------------------------------

st.header("1️⃣ Costos de ingredientes")
st.caption("Maltas, lúpulos, levaduras, adjuntos y agua.")

ing_df = loaded_tables.get("Ingredientes", default_ingredients())

ing_df = st.data_editor(
    ing_df, num_rows="dynamic",
    column_config={"Unidad": st.column_config.SelectboxColumn("Unidad", options=UNITS)},
    use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Packaging ---------------------------------------------------------------
# ---------------------------------------------------------------------------

st.header("2️⃣ Costos de packaging")
st.caption("Botellas/latas, tapas, etiquetas, cartones, etc.")

pack_df = loaded_tables.get("Packaging", default_packaging())
pack_df = st.data_editor(pack_df, num_rows="dynamic", use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Auxiliares --------------------------------------------------------------
# ---------------------------------------------------------------------------

st.header("3️⃣ Costos de insumos auxiliares y consumibles")
st.caption("Clarificantes, nutrientes, sales, ácidos, CO₂ y limpieza.")

aux_df = loaded_tables.get("Auxiliares", default_aux())
aux_df = st.data_editor(
    aux_df, num_rows="dynamic",
    column_config={"Unidad": st.column_config.SelectboxColumn("Unidad", options=UNITS)},
    use_container_width=True)

# ---------------------------------------------------------------------------
# 4. Energía, mano de obra e indirectos --------------------------------------
# ---------------------------------------------------------------------------

st.header("4️⃣ Energía, mano de obra y otros servicios")
st.caption("Electricidad/vapor, horas de personal, fletes y costos indirectos.")

colE, colL, colF = st.columns(3)
energy_cost = colE.number_input("Energía (ARS $)", 0.0, 10000.0, p("Energia", 300.0))
lab_hours   = colL.number_input("Horas mano de obra", 0.0, 40.0, p("Horas", 6.0))
lab_rate    = colL.number_input("Costo hora (ARS $)", 0.0, 10000.0, p("Costo_hora", 4000.0))
flete       = colF.number_input("Flete insumos (ARS $)", 0.0, 20000.0, p("Flete", 1000.0))
ind_pct     = colF.number_input("Costos indirectos %", 0.0, 30.0, p("Overhead_pct", 10.0), step=0.5)

# ---------------------------------------------------------------------------
# Cálculos -------------------------------------------------------------------
# ---------------------------------------------------------------------------

ing_cost  = (ing_df["Cantidad"] * ing_df["Costo unitario (ARS $)"]).sum()
pack_cost = (pack_df["Unidades"] * pack_df["Costo unitario (ARS $)"]).sum()
aux_cost  = (aux_df["Cantidad"] * aux_df["Costo unitario (ARS $)"]).sum()
lab_cost  = lab_hours * lab_rate

total_var = ing_cost + pack_cost + aux_cost + energy_cost + lab_cost + flete
ind_cost  = total_var * ind_pct / 100

total_lot = total_var + ind_cost
real_volL = vol_batch * (1 - loss_pct / 100)
real_bott = real_volL * 1000 / bottle_ml if bottle_ml else 0

cost_bot = total_lot / real_bott if real_bott else 0
cost_L   = total_lot / real_volL if real_volL else 0

st.markdown("---")
colA, colB, colC = st.columns(3)
colA.metric("Costo total lote", f"ARS ${total_lot:,.0f}")
colB.metric("Costo/botella", f"ARS ${cost_bot:,.1f}")
colC.metric("Costo/L", f"ARS ${cost_L:,.1f}")

# ---------------------------------------------------------------------------
# Descargar CSV --------------------------------------------------------------
# ---------------------------------------------------------------------------

params_out = {
    "Titulo_lote": lot_title,
    "Volumen_L": vol_batch,
    "Bottle_ml": bottle_ml,
    "Merma_pct": loss_pct,
    "Energia": energy_cost,
    "Horas": lab_hours,
    "Costo_hora": lab_rate,
    "Flete": flete,
    "Overhead_pct": ind_pct,
}

csv_df = build_save_df(params_out, ing_df, pack_df, aux_df)
buffer = io.BytesIO()
csv_df.to_csv(buffer, index=False)

st.download_button("📥 Descargar CSV", buffer.getvalue(), "costos_lote.csv", "text/csv")
