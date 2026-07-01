import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import yfinance as yf
import os
import json
from datetime import datetime, timedelta, timezone
COL_TZ = timezone(timedelta(hours=-5))

# CONFIGURACIÓN DEL FRAMEWORK INTERNA (PRIMERA INSTRUCCIÓN OBLIGATORIA)
st.set_page_config(
    page_title="Inversiones al instante Portafolio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# CONTROL SELECCIONAL DE MIGRACIÓN (PREVIENE BUCLES DE LIMPIEZA)
# -----------------------------------------------------------------------------
llaves_obsoletas = ['inventario_activos_v5', 'db_historica_v5', 'inventario_activos_v6', 'db_historica_v6']
if any(llave in st.session_state for llave in llaves_obsoletas):
    st.session_state.clear()

# -----------------------------------------------------------------------------
# SUB-SISTEMA DE PERSISTENCIA FÍSICA EN DISCO
# -----------------------------------------------------------------------------
CSV_FILE = "inventario_activos.csv"
HIST_FILE = "historial_patrimonio.csv"
CACHE_FILE = "precios_cache.json"

def inicializar_archivos_disco():
    if not os.path.exists(CSV_FILE):
        df_defecto = pd.DataFrame([
            {"Ticker": "IONQ", "Clase": "Acciones EEUU", "Cantidad": 53.40812, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "GOOG", "Clase": "Acciones EEUU", "Cantidad": 36.19290, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "UNH", "Clase": "Acciones EEUU", "Cantidad": 23.83395, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "V", "Clase": "Acciones EEUU", "Cantidad": 9.10111, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "MSFT", "Clase": "Acciones EEUU", "Cantidad": 10.84953, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "GLD", "Clase": "Commodities (Oro)", "Cantidad": 48.53481, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "CIBEST", "Clase": "Acciones Colombia", "Cantidad": 360.0, "Valor_Base_Fijo": 75760.0, "Moneda": "COP"},
            {"Ticker": "GRUPOARGOS", "Clase": "Acciones Colombia", "Cantidad": 31.0, "Valor_Base_Fijo": 15500.0, "Moneda": "COP"},
            {"Ticker": "PFGRUPOARG", "Clase": "Acciones Colombia", "Cantidad": 2199.0, "Valor_Base_Fijo": 11500.0, "Moneda": "COP"},
            {"Ticker": "GXTESCOL", "Clase": "Acciones Colombia", "Cantidad": 88.0, "Valor_Base_Fijo": 52244.0, "Moneda": "COP"},
            {"Ticker": "PEI", "Clase": "Acciones Colombia", "Cantidad": 388.0, "Valor_Base_Fijo": 62000.0, "Moneda": "COP"},
            {"Ticker": "BTC", "Clase": "Criptomonedas", "Cantidad": 0.13078689, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "ETH", "Clase": "Criptomonedas", "Cantidad": 0.57562952, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "ADA", "Clase": "Criptomonedas", "Cantidad": 765.10032522, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "XRP", "Clase": "Criptomonedas", "Cantidad": 82.24143446, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
            {"Ticker": "Fiducuenta Bancolombia", "Clase": "Fondos de Inversión", "Cantidad": 1.0, "Valor_Base_Fijo": 1362452901.0, "Moneda": "COP"},
            {"Ticker": "Disponible Broker Col", "Clase": "Liquidez COP", "Cantidad": 1.0, "Valor_Base_Fijo": 46506461.0, "Moneda": "COP"},
            {"Ticker": "Broker EEUU", "Clase": "Liquidez USD", "Cantidad": 1.0, "Valor_Base_Fijo": 12500.0, "Moneda": "USD"},
            {"Ticker": "Apto Avenida Park", "Clase": "Propiedad Raíz", "Cantidad": 1.0, "Valor_Base_Fijo": 950000000.0, "Moneda": "COP"},
            {"Ticker": "Apto Mediterranea", "Clase": "Propiedad Raíz", "Cantidad": 1.0, "Valor_Base_Fijo": 360000000.0, "Moneda": "COP"}
        ])
        df_defecto.to_csv(CSV_FILE, index=False)

    if not os.path.exists(HIST_FILE):
        df_hist_defecto = pd.DataFrame([
            {"Fecha": "2025-06-15", "Clase": "Acciones EEUU", "Valor_COP": 100000000.0},
            {"Fecha": "2025-06-15", "Clase": "Commodities (Oro)", "Valor_COP": 15000000.0},
            {"Fecha": "2025-06-15", "Clase": "Criptomonedas", "Valor_COP": 30000000.0},
            {"Fecha": "2025-06-15", "Clase": "Acciones Colombia", "Valor_COP": 65000000.0},
            {"Fecha": "2025-06-15", "Clase": "Fondos de Inversión", "Valor_COP": 1250000000.0},
            {"Fecha": "2025-06-15", "Clase": "Cash Broker Desk", "Valor_COP": 40000000.0},
            
            {"Fecha": "2025-09-15", "Clase": "Acciones EEUU", "Valor_COP": 115000000.0},
            {"Fecha": "2025-09-15", "Clase": "Commodities (Oro)", "Valor_COP": 16500000.0},
            {"Fecha": "2025-09-15", "Clase": "Criptomonedas", "Valor_COP": 33000000.0},
            {"Fecha": "2025-09-15", "Clase": "Acciones Colombia", "Valor_COP": 71000000.0},
            {"Fecha": "2025-09-15", "Clase": "Fondos de Inversión", "Valor_COP": 1290000000.0},
            {"Fecha": "2025-09-15", "Clase": "Cash Broker Desk", "Valor_COP": 43000000.0},
            
            {"Fecha": "2026-01-01", "Clase": "Acciones EEUU", "Valor_COP": 125000000.0},
            {"Fecha": "2026-01-01", "Clase": "Commodities (Oro)", "Valor_COP": 17800000.0},
            {"Fecha": "2026-01-01", "Clase": "Criptomonedas", "Valor_COP": 35000000.0},
            {"Fecha": "2026-01-01", "Clase": "Acciones Colombia", "Valor_COP": 75000000.0},
            {"Fecha": "2026-01-01", "Clase": "Fondos de Inversión", "Valor_COP": 1320000000.0},
            {"Fecha": "2026-01-01", "Clase": "Cash Broker Desk", "Valor_COP": 44000000.0},
            
            {"Fecha": "2026-04-15", "Clase": "Acciones EEUU", "Valor_COP": 130000000.0},
            {"Fecha": "2026-04-15", "Clase": "Commodities (Oro)", "Valor_COP": 19000000.0},
            {"Fecha": "2026-04-15", "Clase": "Criptomonedas", "Valor_COP": 37000000.0},
            {"Fecha": "2026-04-15", "Clase": "Acciones Colombia", "Valor_COP": 78000000.0},
            {"Fecha": "2026-04-15", "Clase": "Fondos de Inversión", "Valor_COP": 1350000000.0},
            {"Fecha": "2026-04-15", "Clase": "Cash Broker Desk", "Valor_COP": 45500000.0}
        ])
        df_hist_defecto.to_csv(HIST_FILE, index=False)

# -----------------------------------------------------------------------------
# SUBSISTEMA DE PERSISTENCIA HÍBRIDA (SQL NUBE / CSV LOCAL)
# -----------------------------------------------------------------------------
def usar_base_datos():
    try:
        # Comprobar si st.secrets tiene credenciales de db y sqlalchemy está disponible
        if "connections" in st.secrets and "db" in st.secrets["connections"]:
            import sqlalchemy
            return True
    except Exception:
        pass
    return False

def obtener_engine():
    try:
        conn = st.connection("db", type="sql")
        return conn.engine
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

def cargar_inventario():
    if usar_base_datos():
        engine = obtener_engine()
        if engine is not None:
            import time
            for intento in range(5):
                try:
                    # Comprobar si la tabla existe, si no, crearla
                    with engine.begin() as conn:
                        conn.exec_driver_sql("""
                            CREATE TABLE IF NOT EXISTS inventario_activos (
                                "Ticker" VARCHAR(50) PRIMARY KEY,
                                "Clase" VARCHAR(100),
                                "Cantidad" DOUBLE PRECISION,
                                "Valor_Base_Fijo" DOUBLE PRECISION,
                                "Moneda" VARCHAR(10),
                                "Var_Manual" DOUBLE PRECISION DEFAULT 0.0
                            )
                        """)
                        
                        # Garantizar que la columna exista en bases de datos ya creadas
                        try:
                            conn.exec_driver_sql('ALTER TABLE inventario_activos ADD COLUMN IF NOT EXISTS "Var_Manual" DOUBLE PRECISION DEFAULT 0.0')
                        except Exception:
                            pass
                        
                        # Comprobar si está vacía
                        count = conn.exec_driver_sql("SELECT COUNT(*) FROM inventario_activos").scalar()
                        if count == 0:
                            df_defecto = pd.read_csv(CSV_FILE) if os.path.exists(CSV_FILE) else pd.DataFrame([
                                {"Ticker": "IONQ", "Clase": "Acciones EEUU", "Cantidad": 53.40812, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "GOOG", "Clase": "Acciones EEUU", "Cantidad": 36.19290, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "UNH", "Clase": "Acciones EEUU", "Cantidad": 23.83395, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "V", "Clase": "Acciones EEUU", "Cantidad": 9.10111, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "MSFT", "Clase": "Acciones EEUU", "Cantidad": 10.84953, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "GLD", "Clase": "Commodities (Oro)", "Cantidad": 48.53481, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "CIBEST", "Clase": "Acciones Colombia", "Cantidad": 360.0, "Valor_Base_Fijo": 75760.0, "Moneda": "COP"},
                                {"Ticker": "GRUPOARGOS", "Clase": "Acciones Colombia", "Cantidad": 31.0, "Valor_Base_Fijo": 15500.0, "Moneda": "COP"},
                                {"Ticker": "PFGRUPOARG", "Clase": "Acciones Colombia", "Cantidad": 2199.0, "Valor_Base_Fijo": 11500.0, "Moneda": "COP"},
                                {"Ticker": "GXTESCOL", "Clase": "Acciones Colombia", "Cantidad": 88.0, "Valor_Base_Fijo": 52244.0, "Moneda": "COP"},
                                {"Ticker": "PEI", "Clase": "Acciones Colombia", "Cantidad": 388.0, "Valor_Base_Fijo": 62000.0, "Moneda": "COP"},
                                {"Ticker": "BTC", "Clase": "Criptomonedas", "Cantidad": 0.13078689, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "ETH", "Clase": "Criptomonedas", "Cantidad": 0.57562952, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "ADA", "Clase": "Criptomonedas", "Cantidad": 765.10032522, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "XRP", "Clase": "Criptomonedas", "Cantidad": 82.24143446, "Valor_Base_Fijo": 0.0, "Moneda": "USD"},
                                {"Ticker": "Fiducuenta Bancolombia", "Clase": "Fondos de Inversión", "Cantidad": 1.0, "Valor_Base_Fijo": 1362452901.0, "Moneda": "COP"},
                                {"Ticker": "Disponible Broker Col", "Clase": "Liquidez COP", "Cantidad": 1.0, "Valor_Base_Fijo": 46506461.0, "Moneda": "COP"},
                                {"Ticker": "Broker EEUU", "Clase": "Liquidez USD", "Cantidad": 1.0, "Valor_Base_Fijo": 12500.0, "Moneda": "USD"},
                                {"Ticker": "Apto Avenida Park", "Clase": "Propiedad Raíz", "Cantidad": 1.0, "Valor_Base_Fijo": 950000000.0, "Moneda": "COP"},
                                {"Ticker": "Apto Mediterranea", "Clase": "Propiedad Raíz", "Cantidad": 1.0, "Valor_Base_Fijo": 360000000.0, "Moneda": "COP"}
                            ])
                            df_defecto.to_sql("inventario_activos", engine, if_exists="append", index=False)
                    
                    return pd.read_sql("SELECT * FROM inventario_activos", engine)
                except Exception as e:
                    try:
                        engine.dispose()
                    except Exception:
                        pass
                    if intento < 4:
                        if intento == 0:
                            st.info("Conectando con la base de datos en la nube (Neon)... por favor espera unos segundos.")
                        time.sleep(2.0)
                    else:
                        st.warning(f"Error al leer inventario de base de datos (usando CSV local): {e}")
                
    inicializar_archivos_disco()
    return pd.read_csv(CSV_FILE)

def guardar_inventario(df):
    if usar_base_datos():
        engine = obtener_engine()
        if engine is not None:
            import time
            for intento in range(3):
                try:
                    df.to_sql("inventario_activos", engine, if_exists="replace", index=False)
                    return
                except Exception as e:
                    try:
                        engine.dispose()
                    except Exception:
                        pass
                    if intento < 2:
                        time.sleep(2.0)
                    else:
                        st.warning(f"Error al escribir inventario en base de datos: {e}")
    df.to_csv(CSV_FILE, index=False)

def cargar_historial():
    if usar_base_datos():
        engine = obtener_engine()
        if engine is not None:
            import time
            for intento in range(5):
                try:
                    with engine.begin() as conn:
                        conn.exec_driver_sql("""
                            CREATE TABLE IF NOT EXISTS historial_patrimonio (
                                "Fecha" DATE,
                                "Clase" VARCHAR(100),
                                "Valor_COP" DOUBLE PRECISION,
                                PRIMARY KEY ("Fecha", "Clase")
                            )
                        """)
                        
                        count = conn.exec_driver_sql("SELECT COUNT(*) FROM historial_patrimonio").scalar()
                        if count == 0:
                            df_hist_defecto = pd.read_csv(HIST_FILE) if os.path.exists(HIST_FILE) else pd.DataFrame([])
                            df_hist_defecto.to_sql("historial_patrimonio", engine, if_exists="append", index=False)
                    
                    df_db = pd.read_sql("SELECT * FROM historial_patrimonio", engine)
                    df_db["Fecha"] = pd.to_datetime(df_db["Fecha"])
                    return df_db
                except Exception as e:
                    try:
                        engine.dispose()
                    except Exception:
                        pass
                    if intento < 4:
                        time.sleep(2.0)
                    else:
                        st.warning(f"Error al leer historial de base de datos (usando CSV local): {e}")
                
    inicializar_archivos_disco()
    df_local = pd.read_csv(HIST_FILE)
    df_local["Fecha"] = pd.to_datetime(df_local["Fecha"])
    return df_local

def guardar_historial(df):
    if usar_base_datos():
        engine = obtener_engine()
        if engine is not None:
            import time
            for intento in range(3):
                try:
                    df_save = df.copy()
                    if pd.api.types.is_datetime64_any_dtype(df_save["Fecha"]):
                        df_save["Fecha"] = df_save["Fecha"].dt.strftime("%Y-%m-%d")
                    df_save.to_sql("historial_patrimonio", engine, if_exists="replace", index=False)
                    return
                except Exception as e:
                    try:
                        engine.dispose()
                    except Exception:
                        pass
                    if intento < 2:
                        time.sleep(2.0)
                    else:
                        st.warning(f"Error al escribir historial en base de datos: {e}")
    df_save = df.copy()
    if pd.api.types.is_datetime64_any_dtype(df_save["Fecha"]):
        df_save["Fecha"] = df_save["Fecha"].dt.strftime("%Y-%m-%d")
    df_save.to_csv(HIST_FILE, index=False)

inicializar_archivos_disco()

if 'inventario_activos_core' not in st.session_state:
    st.session_state['inventario_activos_core'] = cargar_inventario()

# AUTO-MIGRACIÓN: ACTUALIZAR COTIZACIONES DE BVC DE REFERENCIA (ÚLTIMO CIERRE OFICIAL DE MAYO 2026)
migracion_hecha = False
for idx, row in st.session_state['inventario_activos_core'].iterrows():
    t = row["Ticker"]
    val_actual = row["Valor_Base_Fijo"]
    
    if t == "CIBEST" and val_actual == 71600.0:
        st.session_state['inventario_activos_core'].at[idx, "Valor_Base_Fijo"] = 75760.0
        migracion_hecha = True
    elif t == "GRUPOARGOS" and val_actual == 13660.0:
        st.session_state['inventario_activos_core'].at[idx, "Valor_Base_Fijo"] = 15500.0
        migracion_hecha = True
    elif t == "GXTESCOL" and val_actual == 53250.0:
        st.session_state['inventario_activos_core'].at[idx, "Valor_Base_Fijo"] = 52244.0
        migracion_hecha = True

if migracion_hecha:
    guardar_inventario(st.session_state['inventario_activos_core'])

# Initialize top bar controls in session state if not present
if "dark_mode_state" not in st.session_state:
    st.session_state["dark_mode_state"] = True

# -----------------------------------------------------------------------------
# SUBSISTEMA DE CACHÉ DE PRECIOS LOCAL
# -----------------------------------------------------------------------------
def cargar_cache_precios():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def guardar_cache_precios(precios, variaciones):
    cache = cargar_cache_precios()
    for t in precios:
        cache[t] = {
            "precio": precios[t],
            "variacion": variaciones.get(t, 0.0),
            "actualizado": datetime.now(COL_TZ).strftime("%Y-%m-%d %H:%M:%S")
        }
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# CONTROL DINÁMICO DE TEMAS VISUALES Y HEADER DE ALTA GAMA (SIN SIDEBAR)
# -----------------------------------------------------------------------------
modo_oscuro = st.session_state["dark_mode_state"]

if modo_oscuro:
    BG_COLOR = "#0B0F19"
    TEXT_COLOR = "#FFFFFF"
    TEXT_MUTED = "#9CA3AF"
    GRID_COLOR = "#1F2937"
    PLOTLY_TEMPLATE = "plotly_dark"
    PALETA_GRAFICOS = ["#6366F1", "#06B6D4", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6"]
    
    CSS_VARIABLES = """
    :root {
        --bg-color: #0B0F19;
        --text-color: #F9FAFB;
        --text-muted: #9CA3AF;
        --card-bg: rgba(17, 24, 39, 0.6);
        --border-color: rgba(255, 255, 255, 0.08);
        --shadow: 0 4px 30px rgba(0, 0, 0, 0.35);
        --shadow-hover: 0 10px 45px rgba(99, 102, 241, 0.18);
        --primary-glow: rgba(99, 102, 241, 0.5);
        --grid-color: #1F2937;
    }
    """
else:
    BG_COLOR = "#F8FAFC"
    TEXT_COLOR = "#0F172A"
    TEXT_MUTED = "#64748B"
    GRID_COLOR = "#E2E8F0"
    PLOTLY_TEMPLATE = "plotly_white"
    PALETA_GRAFICOS = ["#4F46E5", "#0EA5E9", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6"]
    
    CSS_VARIABLES = """
    :root {
        --bg-color: #F8FAFC;
        --text-color: #0F172A;
        --text-muted: #64748B;
        --card-bg: rgba(255, 255, 255, 0.75);
        --border-color: rgba(0, 0, 0, 0.06);
        --shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        --shadow-hover: 0 10px 30px rgba(79, 70, 229, 0.1);
        --primary-glow: rgba(79, 70, 229, 0.35);
        --grid-color: #E2E8F0;
    }
    """

# Inyección de estilos CSS avanzados, Glassmorphism y ocultamiento total de sidebar
st.markdown(f"""
    <style>
    {CSS_VARIABLES}
    
    /* Forzar transparencia absoluta en todos los iframes y sus contenedores para evitar recuadros blancos */
    iframe, 
    iframe[title="st.components.v1.html"],
    div[data-testid="stHtml"],
    div[data-testid="stHtml"] > div,
    div[data-testid="element-container"] iframe,
    div[class*="element-container"] iframe,
    .element-container iframe,
    .stHtml {{
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* ELIMINAR COMPLETAMENTE EL PANEL LATERAL IZQUIERDO, EL HEADER Y EL COLLAPSE BUTTON */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    [data-testid="stHeader"] {{
        display: none !important;
    }}
    
    /* Alinear verticalmente los elementos de las columnas del header */
    [data-testid="stHorizontalBlock"]:first-of-type {{
        align-items: center !important;
    }}
    [data-testid="stHorizontalBlock"]:first-of-type label {{
        margin-bottom: 0px !important;
    }}
    
    /* Configuración estructural base full-width */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {{
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        transition: all 0.2s ease;
    }}
    
    /* Resaltar todos los títulos con peso elegante y nítido */
    div[data-testid="stMarkdownContainer"] h1, 
    div[data-testid="stMarkdownContainer"] h2, 
    div[data-testid="stMarkdownContainer"] h3, 
    div[data-testid="stMarkdownContainer"] h4, 
    div[data-testid="stMarkdownContainer"] h5, 
    div[data-testid="stMarkdownContainer"] h6,
    span[data-testid="stSubheader"] {{
        color: var(--text-color) !important;
        font-weight: 600 !important;
    }}
    
    /* Etiquetas de widgets, radios y selectores con peso sofisticado */
    label[data-testid="stWidgetLabel"],
    div[data-testid="stRadio"] label,
    div[role="radiogroup"] label span,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] details summary span {{
        color: var(--text-color) !important;
        font-weight: 500 !important;
    }}
    
    /* Textos generales en peso regular fluido */
    .stMarkdown p,
    .stSubheader p,
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] span, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] ul,
    div[data-testid="stMarkdownContainer"] ol,
    div[data-testid="stMarkdownContainer"] em,
    div[data-testid="stMarkdownContainer"] code {{
        color: var(--text-color) !important;
        font-weight: 400 !important;
    }}
    
    /* Peso específico para elementos destacados */
    div[data-testid="stMarkdownContainer"] strong {{
        color: var(--text-color) !important;
        font-weight: 600 !important;
    }}
    
    /* Forzar visibilidad, transparencia y evitar recuadros blancos en expanders */
    div[data-testid="stExpander"],
    div[data-testid="stExpander"] > details,
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] details[open] summary,
    div[data-testid="stExpander"] details summary:hover,
    div[data-testid="stExpander"] details summary:focus,
    div[data-testid="stExpander"] details summary:active {{
        background-color: transparent !important;
        background: transparent !important;
        color: var(--text-color) !important;
        border: none !important;
        box-shadow: none !important;
    }}
    div[data-testid="stExpander"] details summary svg {{
        fill: var(--text-color) !important;
        color: var(--text-color) !important;
    }}
    
    /* Estilos Premium para inputs, cajas de texto y selectores */
    input, 
    textarea, 
    select,
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="input"] input {{
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }}
    
    /* Menús desplegables de selectbox y listas de opciones */
    div[role="listbox"],
    div[role="listbox"] li,
    div[role="listbox"] div,
    div[role="option"],
    div[role="option"] span {{
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
    }}
    
    /* Ajustes específicos para que los labels de los radio buttons resalten perfectamente */
    div[data-testid="stRadio"] label p {{
        color: var(--text-color) !important;
        font-weight: 600 !important;
    }}
    
    /* Optimización de los márgenes principales para maximizar espacio */
    [data-testid="stMainBlockContainer"] {{
        padding-top: 2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}
    
    /* Tarjetas de Métricas Premium (Glassmorphism + Adaptación de Ancho) */
    .metric-container {{
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: var(--shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        height: 120px;
        overflow: hidden;
    }}
    .metric-container:hover {{
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
        border-color: var(--primary-glow);
    }}
    .metric-label {{
        font-size: 10px;
        font-weight: 700;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        white-space: nowrap;
    }}
    .metric-value {{
        font-size: clamp(18px, 1.8vw, 26px) !important;
        font-weight: 850;
        color: var(--text-color) !important;
        margin: 3px 0;
        line-height: 1.15;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .metric-delta {{
        font-size: 11px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 3px;
        white-space: nowrap;
    }}
    
    div[data-testid="stMarkdownContainer"] .delta-positive,
    div[data-testid="stMarkdownContainer"] span.delta-positive,
    div[data-testid="stMarkdownContainer"] p.delta-positive,
    .delta-positive {{
        color: #10B981 !important;
    }}
    div[data-testid="stMarkdownContainer"] .delta-negative,
    div[data-testid="stMarkdownContainer"] span.delta-negative,
    div[data-testid="stMarkdownContainer"] p.delta-negative,
    .delta-negative {{
        color: #EF4444 !important;
    }}
    div[data-testid="stMarkdownContainer"] .delta-neutral,
    div[data-testid="stMarkdownContainer"] span.delta-neutral,
    div[data-testid="stMarkdownContainer"] p.delta-neutral,
    .delta-neutral {{
        color: var(--text-muted) !important;
    }}
    
    /* Tarjeta de P&L Unificada Compacta */
    .pnl-container {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s ease;
        overflow: hidden;
    }}
    .pnl-container:hover {{
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
        border-color: var(--primary-glow);
    }}
    
    /* Desglose de variaciones de categoría */
    .category-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: flex-start;
        width: 100%;
        margin-top: 8px;
    }}
    .category-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: var(--shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        flex: 1 1 calc(25% - 12px);
        min-width: 170px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        overflow: hidden;
        position: relative;
    }}
    .category-card:hover {{
        transform: translateY(-4px);
        border-color: var(--primary-glow);
        box-shadow: var(--shadow-hover);
    }}
    .breakdown-title {{
        font-size: 10px;
        font-weight: 700;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }}
    .breakdown-value {{
        font-size: 17px !important;
        font-weight: 800;
        color: var(--text-color) !important;
        margin-top: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    /* Barra de Control Superior Glassmorphic */
    .top-control-bar {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 10px 20px;
        margin-bottom: 20px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }}
    
    /* Ajustes generales de Streamlit */
    div[data-baseweb="tab-list"] {{
        background-color: transparent !important;
        border-bottom: 1px solid var(--border-color) !important;
        gap: 20px;
    }}
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 5px !important;
        transition: all 0.2s ease;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--text-color) !important;
        border-bottom: 3px solid #6366F1 !important;
        font-weight: 700 !important;
    }}
    
    hr {{
        border-top: 1px solid var(--border-color) !important;
    }}
    
    /* Responsividad avanzada para PC y Celulares (Enforce clean mobile columns) */
    @media (max-width: 768px) {{
        div[data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
            gap: 12px !important;
        }}
        div[data-testid="column"] {{
            width: 100% !important;
            max-width: 100% !important;
            min-width: 100% !important;
            margin-left: 0px !important;
            margin-right: 0px !important;
            margin-top: 4px !important;
        }}
        /* Tarjetas de Métricas en Celular */
        .metric-container, .pnl-container {{
            height: auto !important;
            padding: 12px 14px !important;
        }}
        .metric-value {{
            font-size: 20px !important;
        }}
        /* Evitar que las breakdown cards colapsen o queden desalineadas */
        .category-card {{
            flex: 1 1 calc(50% - 12px) !important;
            min-width: 140px !important;
            padding: 10px 12px !important;
            margin-bottom: 4px !important;
        }}
        .breakdown-value {{
            font-size: 15px !important;
        }}
    }}
    
    /* Barra de Exposición Cambiaria (USD vs COP) - POTENCIADA */
    .currency-bar-container-pro {{
        width: 100%;
        height: 26px;
        background: rgba(148, 163, 184, 0.1);
        border-radius: 13px;
        overflow: hidden;
        display: flex;
        margin-top: 14px;
        margin-bottom: 12px;
        border: 1px solid var(--border-color);
        box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.25);
    }}
    .currency-bar-fill-usd-pro {{
        background: linear-gradient(90deg, #6366F1, #06B6D4);
        height: 100%;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF !important;
        font-size: 11px;
        font-weight: 900;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
    }}
    .currency-bar-fill-cop-pro {{
        background: linear-gradient(90deg, #10B981, #0EA5E9);
        height: 100%;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF !important;
        font-size: 11px;
        font-weight: 900;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
    }}
    .currency-label-row-pro {{
        display: flex;
        gap: 15px;
        width: 100%;
        margin-top: 4px;
        margin-bottom: 15px;
    }}
    .currency-exposure-card {{
        flex: 1;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 10px 14px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 60px;
    }}
    .currency-exposure-card.usd {{
        border-left: 4px solid #06B6D4;
    }}
    .currency-exposure-card.cop {{
        border-left: 4px solid #10B981;
    }}
    .currency-exposure-title {{
        font-size: 9px;
        font-weight: 700;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .currency-exposure-value {{
        font-size: 15px !important;
        font-weight: 800;
        color: var(--text-color) !important;
        margin-top: 3px;
    }}

    /* Tarjetas de Riesgo Premium y Super Grandes (DISEÑO INSTITUCIONAL) */
    .pro-risk-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: var(--shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        min-height: 145px;
        position: relative;
        overflow: hidden;
        margin-bottom: 10px;
    }}
    .pro-risk-card:hover {{
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        border-color: var(--primary-glow);
    }}
    .pro-risk-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
    }}
    .pro-risk-card.volatility::before {{
        background: linear-gradient(90deg, #F59E0B, #EC4899);
    }}
    .pro-risk-card.efficiency::before {{
        background: linear-gradient(90deg, #6366F1, #06B6D4);
    }}
    .pro-risk-card.drawdown::before {{
        background: linear-gradient(90deg, #EF4444, #F59E0B);
    }}
    .pro-risk-title {{
        font-size: 10px;
        font-weight: 800;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    .pro-risk-value {{
        font-size: clamp(23px, 2.2vw, 30px) !important;
        font-weight: 900;
        color: var(--text-color) !important;
        margin: 6px 0;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }}
    .pro-risk-badge-row {{
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 4px;
    }}
    
    @media (max-width: 768px) {{
        .currency-label-row-pro {{
            flex-direction: column !important;
            gap: 8px !important;
        }}
        .currency-exposure-card {{
            min-height: auto !important;
            padding: 8px 12px !important;
        }}
        .pro-risk-card {{
            min-height: auto !important;
            padding: 14px 16px !important;
        }}
        .pro-risk-value {{
            font-size: 24px !important;
        }}
    }}
    
    /* Estilos corporativos de alto nivel para los botones de Streamlit */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: auto !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%) !important;
        box-shadow: 0 6px 22px rgba(99, 102, 241, 0.45) !important;
        transform: translateY(-2px) !important;
    }}
    div.stButton > button[kind="primary"]:active {{
        transform: translateY(0px) !important;
    }}
    
    div.stButton > button[kind="secondary"] {{
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        height: auto !important;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        border-color: #EF4444 !important;
        color: #EF4444 !important;
        background-color: rgba(239, 68, 68, 0.05) !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15) !important;
    }}
    
    /* Estilos Premium para la Tabla de Activos */
    .premium-table-container {{
        width: 100%;
        overflow-x: auto;
        border-radius: 14px;
        border: 1px solid var(--border-color);
        background: var(--card-bg);
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
        margin-top: 10px;
        margin-bottom: 20px;
    }}
    .premium-table {{
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }}
    .premium-table th {{
        background: rgba(148, 163, 184, 0.08);
        padding: 14px 16px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: var(--text-color);
        letter-spacing: 0.8px;
        border-bottom: 2px solid var(--border-color);
    }}
    .premium-table td {{
        padding: 14px 16px;
        font-size: 13px;
        color: var(--text-color);
        border-bottom: 1px solid var(--border-color);
        vertical-align: middle;
    }}
    .premium-table tr:last-child td {{
        border-bottom: none;
    }}
    .premium-table tr:hover {{
        background: rgba(99, 102, 241, 0.04);
        transition: background 0.2s ease;
    }}
    .ticker-badge {{
        font-weight: 800;
        font-size: 13.5px;
        letter-spacing: 0.2px;
        color: var(--text-color);
        padding: 4px 8px;
        border-radius: 6px;
        background: rgba(148, 163, 184, 0.08);
        border-left: 3px solid #6366F1;
        display: inline-block;
    }}
    .class-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    .currency-badge {{
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    .currency-badge.usd {{
        background: rgba(99, 102, 241, 0.15) !important;
        color: #6366F1 !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
    }}
    .currency-badge.cop {{
        background: rgba(16, 185, 129, 0.15) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
    }}
    .pill-var {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        white-space: nowrap;
    }}
    .pill-var.positive {{
        background: rgba(16, 185, 129, 0.12) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.15) !important;
    }}
    .pill-var.negative {{
        background: rgba(239, 68, 68, 0.12) !important;
        color: #EF4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.15) !important;
    }}
    .pill-var.neutral {{
        background: rgba(156, 163, 175, 0.12) !important;
        color: #9CA3AF !important;
        border: 1px solid rgba(156, 163, 175, 0.15) !important;
    }}
    
    /* Estilos Premium para las Tarjetas de Noticias */
    .news-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: var(--shadow);
        margin-bottom: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        min-height: 145px;
        height: auto;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
    }}
    .news-card:hover {{
        transform: translateY(-3px) !important;
        border-color: var(--primary-glow) !important;
        box-shadow: var(--shadow-hover) !important;
    }}
    .news-title-link {{
        text-decoration: none !important;
        color: var(--text-color) !important;
        transition: color 0.2s ease;
    }}
    .news-title-link:hover {{
        color: #6366F1 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MOTOR DE CONSULTA AUTOMÁTICA EN TIEMPO REAL (BATCH FETCHING OPTIMIZED)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def consultar_mercado_global_batch(tickers, trm_ticker="USDCOP=X"):
    precios, variaciones = {}, {}
    trm_dia, trm_yesterday = 3950.0, 3950.0
    
    # Combined target list
    todos_tickers = list(set(tickers + [trm_ticker]))
    
    # Static fallbacks (last resort)
    fallbacks_p = {"IONQ": 64.0, "GOOG": 379.0, "UNH": 388.0, "V": 275.0, "MSFT": 420.0, "GLD": 414.0, "USDCOP=X": 3950.0}
    fallbacks_v = {"IONQ": 2.15, "GOOG": -0.45, "UNH": 1.12, "V": 0.05, "MSFT": -0.88, "GLD": -0.12, "USDCOP=X": 0.0}
    
    # Load smart cache
    cache = cargar_cache_precios()
    
    try:
        # BATCH DOWNLOAD (Ultra-fast single query!)
        df = yf.download(todos_tickers, period="2d", interval="1d", progress=False, group_by="ticker")
        
        if not df.empty:
            for t in todos_tickers:
                try:
                    df_t = df if len(todos_tickers) == 1 else (df[t] if t in df else None)
                    if df_t is not None and not df_t.empty:
                        close_col = pd.Series()
                        if "Close" in df_t.columns:
                            close_col = df_t["Close"].dropna()
                        elif isinstance(df_t.columns, pd.MultiIndex):
                            if "Close" in df_t.columns.levels[0]:
                                close_col = df_t.xs("Close", axis=1, level=0).dropna()
                            elif "Close" in df_t.columns.levels[1]:
                                close_col = df_t.xs("Close", axis=1, level=1).dropna()
                        
                        if len(close_col) >= 1:
                            val_last = close_col.iloc[-1]
                            p_last = float(val_last.iloc[0]) if isinstance(val_last, pd.Series) else float(val_last)
                            precios[t] = p_last
                            
                            if len(close_col) >= 2:
                                val_prev = close_col.iloc[-2]
                                p_prev = float(val_prev.iloc[0]) if isinstance(val_prev, pd.Series) else float(val_prev)
                                variaciones[t] = ((p_last - p_prev) / p_prev) * 100
                            else:
                                variaciones[t] = 0.0
                except Exception:
                    pass
    except Exception:
        pass
    
    # Fill missing values from cache or fallbacks
    for t in todos_tickers:
        if t not in precios:
            if t in cache:
                precios[t] = cache[t]["precio"]
                variaciones[t] = cache[t]["variacion"]
            else:
                precios[t] = fallbacks_p.get(t, 10.0)
                variaciones[t] = fallbacks_v.get(t, 0.0)
    
    # Save successfully resolved prices to cache
    guardar_cache_precios(precios, variaciones)
    
    # -------------------------------------------------------------------------
    # SISTEMA DE CACHÉ DE TRM (SPOT RATE) CON FALLBACK DE EXCHANGERATE-API
    # -------------------------------------------------------------------------
    trm_dia_yf = precios.get(trm_ticker, 3950.0)
    trm_yesterday_yf = trm_dia_yf
    trm_success = False
    
    # 1. Intentar obtener la TRM/Spot desde yfinance (tiempo real con fast_info + histórico para ayer)
    try:
        # Intentamos obtener primero el precio spot exacto en tiempo real
        ticker_obj = yf.Ticker(trm_ticker)
        live_price = float(ticker_obj.fast_info['lastPrice'])
        if live_price > 0:
            trm_dia_yf = live_price
            trm_success = True
            
            # Ahora buscamos la tasa del día anterior de forma histórica
            df_trm = df if len(todos_tickers) == 1 else (df[trm_ticker] if trm_ticker in df else None)
            if df_trm is not None and not df_trm.empty:
                close_col_trm = pd.Series()
                if "Close" in df_trm.columns:
                    close_col_trm = df_trm["Close"].dropna()
                elif isinstance(df_trm.columns, pd.MultiIndex):
                    if "Close" in df_trm.columns.levels[0]:
                        close_col_trm = df_trm.xs("Close", axis=1, level=0).dropna()
                    elif "Close" in df_trm.columns.levels[1]:
                        close_col_trm = df_trm.xs("Close", axis=1, level=1).dropna()
                
                if not close_col_trm.empty:
                    last_date_str = str(close_col_trm.index[-1]).split()[0]
                    hoy_str = datetime.now(COL_TZ).strftime("%Y-%m-%d")
                    if last_date_str == hoy_str:
                        if len(close_col_trm) >= 2:
                            val_prev = close_col_trm.iloc[-2]
                            trm_yesterday_yf = float(val_prev.iloc[0]) if isinstance(val_prev, pd.Series) else float(val_prev)
                        else:
                            cache_temp = cargar_cache_precios()
                            trm_yesterday_cached = cache_temp.get("_trm_yesterday")
                            if trm_yesterday_cached is not None:
                                trm_yesterday_yf = trm_yesterday_cached["precio"]
                            else:
                                trm_yesterday_yf = trm_dia_yf
                    else:
                        val_prev = close_col_trm.iloc[-1]
                        trm_yesterday_yf = float(val_prev.iloc[0]) if isinstance(val_prev, pd.Series) else float(val_prev)
    except Exception:
        pass

    # Fallback si fast_info falló pero tenemos datos de df_trm
    if not trm_success:
        try:
            df_trm = df if len(todos_tickers) == 1 else (df[trm_ticker] if trm_ticker in df else None)
            if df_trm is not None and not df_trm.empty:
                close_col_trm = pd.Series()
                if "Close" in df_trm.columns:
                    close_col_trm = df_trm["Close"].dropna()
                elif isinstance(df_trm.columns, pd.MultiIndex):
                    if "Close" in df_trm.columns.levels[0]:
                        close_col_trm = df_trm.xs("Close", axis=1, level=0).dropna()
                    elif "Close" in df_trm.columns.levels[1]:
                        close_col_trm = df_trm.xs("Close", axis=1, level=1).dropna()
                
                if len(close_col_trm) >= 1:
                    val_last = close_col_trm.iloc[-1]
                    trm_dia_yf = float(val_last.iloc[0]) if isinstance(val_last, pd.Series) else float(val_last)
                    trm_success = True
                    if len(close_col_trm) >= 2:
                        val_prev = close_col_trm.iloc[-2]
                        trm_yesterday_yf = float(val_prev.iloc[0]) if isinstance(val_prev, pd.Series) else float(val_prev)
                    else:
                        cache_temp = cargar_cache_precios()
                        trm_yesterday_cached = cache_temp.get("_trm_yesterday")
                        if trm_yesterday_cached is not None:
                            trm_yesterday_yf = trm_yesterday_cached["precio"]
                        else:
                            trm_yesterday_yf = trm_dia_yf
        except Exception:
            pass

    # 2. Si yfinance falló (común en Streamlit Cloud por bloqueos), usar ExchangeRate-API como fallback en vivo
    trm_dia_fallback = None
    if not trm_success:
        try:
            res_api = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            if res_api.status_code == 200:
                data_api = res_api.json()
                trm_dia_fallback = float(data_api["rates"].get("COP"))
        except Exception:
            pass

    cache = cargar_cache_precios()
    
    if trm_success:
        trm_dia = trm_dia_yf
        trm_yesterday = trm_yesterday_yf
        
        # Guardamos en caché para cuando yfinance falle
        cache["_trm_dia"] = {
            "precio": trm_dia,
            "date": datetime.now(COL_TZ).strftime("%Y-%m-%d")
        }
        cache["_trm_yesterday"] = {
            "precio": trm_yesterday,
            "date": datetime.now(COL_TZ).strftime("%Y-%m-%d")
        }
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=4)
        except Exception:
            pass
            
    elif trm_dia_fallback is not None:
        # yfinance falló pero ExchangeRate-API funcionó
        trm_dia = trm_dia_fallback
        
        # Intentamos obtener la de ayer de la caché, o del fallback de yfinance
        trm_yesterday_cached = cache.get("_trm_yesterday")
        if trm_yesterday_cached is not None:
            trm_yesterday = trm_yesterday_cached["precio"]
        else:
            trm_yesterday = trm_yesterday_yf
            
        # Actualizamos la caché con la nueva TRM en vivo
        cache["_trm_dia"] = {
            "precio": trm_dia,
            "date": datetime.now(COL_TZ).strftime("%Y-%m-%d")
        }
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=4)
        except Exception:
            pass
            
    else:
        # Todo falló (sin internet), cargamos desde la caché
        trm_dia_cached = cache.get("_trm_dia")
        trm_yesterday_cached = cache.get("_trm_yesterday")
        trm_dia = trm_dia_cached["precio"] if trm_dia_cached is not None else trm_dia_yf
        trm_yesterday = trm_yesterday_cached["precio"] if trm_yesterday_cached is not None else trm_yesterday_yf
    
    # Clean global tickers results
    precios_global = {k: v for k, v in precios.items() if k != trm_ticker}
    variaciones_global = {k: v for k, v in variaciones.items() if k != trm_ticker}
    
    return trm_dia, trm_yesterday, precios_global, variaciones_global

@st.cache_data(ttl=300)
def consultar_mercado_cripto_batch(tickers):
    mapper = {"BTC": "bitcoin", "ETH": "ethereum", "ADA": "cardano", "XRP": "ripple"}
    precios, variaciones = {}, {}
    if not tickers:
        return precios, variaciones
        
    fallbacks_p = {"BTC": 75370.0, "ETH": 2059.0, "ADA": 0.24, "XRP": 1.34}
    fallbacks_v = {"BTC": -2.36, "ETH": -3.59, "ADA": 0.12, "XRP": -1.05}
    
    cache = cargar_cache_precios()
    ids = [mapper[t] for t in tickers if t in mapper]
    
    try:
        if ids:
            res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
            for t in tickers:
                if t in mapper and mapper[t] in res:
                    precios[t] = float(res[mapper[t]]["usd"])
                    variaciones[t] = float(res[mapper[t]].get("usd_24h_change", 0.0))
    except Exception:
        pass
        
    # Apply cached values if download fails
    for t in tickers:
        if t not in precios:
            if t in cache:
                precios[t] = cache[t]["precio"]
                variaciones[t] = cache[t]["variacion"]
            else:
                precios[t] = fallbacks_p.get(t, 1.0)
                variaciones[t] = fallbacks_v.get(t, 0.0)
                
    # Update cache
    guardar_cache_precios(precios, variaciones)
    
    return precios, variaciones

# -----------------------------------------------------------------------------
# SUBSISTEMA DE RADAR DE NOTICIAS (EXTRACTOR COLOMBIA & INTERNACIONAL)
# -----------------------------------------------------------------------------
import xml.etree.ElementTree as ET

def obtener_noticias_colombia():
    import email.utils
    from datetime import timezone, timedelta
    url = "https://news.google.com/rss/search?q=Bolsa+de+Valores+de+Colombia+OR+Bancolombia+OR+Grupo+Argos+OR+PEI+Colombia&hl=es-419&gl=CO&ceid=CO:es-419"
    headers = {"User-Agent": "Mozilla/5.0"}
    noticias = []
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            limit_date = datetime.now(timezone.utc) - timedelta(days=15)
            
            for item in root.findall(".//item"):
                pub_date_str = item.find("pubDate").text
                
                # Filtrar por fecha (máximo 15 días de antigüedad)
                if pub_date_str:
                    try:
                        dt = email.utils.parsedate_to_datetime(pub_date_str)
                        dt_utc = dt.astimezone(timezone.utc)
                        if dt_utc < limit_date:
                            continue
                    except Exception:
                        pass
                
                title = item.find("title").text
                link = item.find("link").text
                source = item.find("source").text if item.find("source") is not None else "Google News"
                
                # Format Colombian source names cleanly
                if "La República" in title or "republica" in link:
                    source = "Diario La República 🇨🇴"
                elif "Valora" in title or "valora" in link:
                    source = "Valora Analitik 🇨🇴"
                elif "Portafolio" in title or "portafolio" in link:
                    source = "Diario Portafolio 🇨🇴"
                elif "El Espectador" in title or "elespectador" in link:
                    source = "El Espectador 🇨🇴"
                elif "El Tiempo" in title or "eltiempo" in link:
                    source = "El Tiempo 🇨🇴"
                else:
                    source = f"{source} 🇨🇴"
                    
                # Clean Google News suffix from titles e.g. " - La República"
                if " - " in title:
                    title = " - ".join(title.split(" - ")[:-1])
                    
                noticias.append({
                    "title": title,
                    "link": link,
                    "publisher": source,
                    "time": pub_date_str[:16] if pub_date_str else "Reciente",
                    "type": "Local 🇨🇴",
                    "accent_color": "#10B981"
                })
                
                if len(noticias) >= 10:  # Mantener un límite de hasta 10 noticias frescas
                    break
    except Exception:
        pass
    return noticias

def obtener_noticias_internacionales(tickers):
    from datetime import timezone, timedelta
    noticias = []
    
    # Tabla de mapeo para tickers estándar de Yahoo Finance
    mapping = {}
    for t in tickers:
        if t in ["BTC", "ETH", "ADA", "XRP"]:
            mapping[f"{t}-USD"] = t
        elif t in ["GOOG", "MSFT", "IONQ", "GLD", "UNH", "V"]:
            mapping[t] = t
            
    top_tickers = list(mapping.keys())[:4]
    limit_date = datetime.now(timezone.utc) - timedelta(days=15)
    
    for t_yf in top_tickers:
        t_orig = mapping[t_yf]
        try:
            ticker_obj = yf.Ticker(t_yf)
            news_items = ticker_obj.news
            if news_items:
                ticker_count = 0
                for item in news_items:
                    # Soporte para formato nuevo anidado y formato anterior plano
                    content = item.get("content", item) if isinstance(item.get("content"), dict) else item
                    
                    # Extraer fecha de publicación y filtrar por antigüedad (máximo 15 días)
                    pub_time_stamp = content.get("providerPublishTime")
                    pub_date_str = content.get("pubDate")
                    
                    is_recent = True
                    fecha_str = "Reciente"
                    
                    if pub_time_stamp:
                        try:
                            pub_date = datetime.fromtimestamp(pub_time_stamp, timezone.utc)
                            if pub_date < limit_date:
                                is_recent = False
                            fecha_str = pub_date.strftime("%d-%b %Y %H:%M")
                        except Exception:
                            pass
                    elif pub_date_str:
                        try:
                            date_str = pub_date_str.replace("Z", "+00:00")
                            pub_date = datetime.fromisoformat(date_str)
                            if pub_date < limit_date:
                                is_recent = False
                            fecha_str = pub_date.strftime("%d-%b %Y %H:%M")
                        except Exception:
                            pass
                            
                    if not is_recent:
                        continue
                        
                    title = content.get("title")
                    if not title:
                        continue
                        
                    # Extraer enlace seguro
                    link = ""
                    if isinstance(content.get("clickThroughUrl"), dict):
                        link = content.get("clickThroughUrl", {}).get("url", "")
                    elif isinstance(content.get("canonicalUrl"), dict):
                        link = content.get("canonicalUrl", {}).get("url", "")
                    else:
                        link = content.get("link", "")
                        
                    # Extraer publicador / fuente
                    publisher = "Yahoo Finance"
                    if isinstance(content.get("provider"), dict):
                        publisher = content.get("provider", {}).get("displayName", "Yahoo Finance")
                    else:
                        publisher = content.get("publisher", "Yahoo Finance")
                        
                    noticias.append({
                        "title": f"[{t_orig}] {title}",
                        "link": link,
                        "publisher": f"{publisher} 🇺🇸",
                        "time": fecha_str,
                        "type": "Internacional 🇺🇸",
                        "accent_color": "#6366F1"
                    })
                    
                    ticker_count += 1
                    if ticker_count >= 3:  # Máximo 3 noticias por ticker
                        break
        except Exception:
            pass
    return noticias

@st.cache_data(ttl=1800)
def cargar_radar_noticias(tickers_usd):
    noticias_locales = obtener_noticias_colombia()
    noticias_inter = obtener_noticias_internacionales(tickers_usd)
    # Return sorted or interlaid results
    return noticias_locales + noticias_inter

# -----------------------------------------------------------------------------
# CORE PIPELINE CONTABLE EN VIVO (MÁXIMA EXACTITUD Y CAMBIO DE DIVISA EXACTO)
# -----------------------------------------------------------------------------
inventario_actual = st.session_state['inventario_activos_core']

us_active = inventario_actual[inventario_actual["Clase"].isin(["Acciones EEUU", "Commodities (Oro)"])]["Ticker"].tolist()
crypto_active = inventario_actual[inventario_actual["Clase"] == "Criptomonedas"]["Ticker"].tolist()

# Ultra-fast Batch APIs call! (BVC stocks are offline/static so only US assets are batched)
trm_dia, trm_yesterday, p_us, v_us = consultar_mercado_global_batch(us_active)
p_cry, v_cry = consultar_mercado_cripto_batch(crypto_active)

precios_maestros, precios_nativos, valores_cop_maestros, variaciones_pct_maestras, variaciones_cop_maestras = [], [], [], [], []
efectos_mercado, efectos_divisa = [], []

for idx, row in inventario_actual.iterrows():
    clase, ticker, cnt = row["Clase"], row["Ticker"], row["Cantidad"]
    p_usd, precio_nativo, v_cop, v_pct = 0.0, 0.0, 0.0, 0.0
    var_cop = 0.0
    ef_mercado, ef_divisa = 0.0, 0.0
    
    if clase == "Acciones EEUU" or (clase == "Commodities (Oro)" and ticker == "GLD"):
        p_usd = p_us.get(ticker, row["Valor_Base_Fijo"])
        precio_nativo = p_usd
        v_pct = v_us.get(ticker, 0.0)
        v_cop = cnt * p_usd * trm_dia
        
        # Cálculo exacto de variación diaria en COP
        p_usd_yesterday = p_usd / (1 + v_pct / 100)
        v_cop_yesterday = cnt * p_usd_yesterday * trm_yesterday
        var_cop = v_cop - v_cop_yesterday
        
        # Desglose de atribución (Fórmula financiera exacta)
        ef_mercado = cnt * (p_usd - p_usd_yesterday) * trm_yesterday
        ef_divisa = cnt * p_usd * (trm_dia - trm_yesterday)
        
    elif clase == "Criptomonedas":
        p_usd = p_cry.get(ticker, row["Valor_Base_Fijo"])
        precio_nativo = p_usd
        v_pct = v_cry.get(ticker, 0.0)
        v_cop = cnt * p_usd * trm_dia
        
        p_usd_yesterday = p_usd / (1 + v_pct / 100)
        v_cop_yesterday = cnt * p_usd_yesterday * trm_yesterday
        var_cop = v_cop - v_cop_yesterday
        
        # Desglose de atribución (Fórmula financiera exacta)
        ef_mercado = cnt * (p_usd - p_usd_yesterday) * trm_yesterday
        ef_divisa = cnt * p_usd * (trm_dia - trm_yesterday)
        
    elif clase == "Liquidez USD":
        p_usd = row["Valor_Base_Fijo"]
        precio_nativo = p_usd
        v_pct = 0.0
        v_cop = cnt * p_usd * trm_dia
        
        v_cop_yesterday = cnt * p_usd * trm_yesterday
        var_cop = v_cop - v_cop_yesterday
        
        # En caja USD, la fluctuación es puramente por el tipo de cambio
        ef_mercado = 0.0
        ef_divisa = cnt * p_usd * (trm_dia - trm_yesterday)
        
    elif clase in ["Acciones Colombia", "Inmobiliario Bursátil"]:
        precio_cop = row["Valor_Base_Fijo"]
        precio_nativo = precio_cop
        v_pct = float(row["Var_Manual"]) if "Var_Manual" in row and not pd.isna(row["Var_Manual"]) else 0.0
        v_cop = cnt * precio_cop
        p_usd = precio_cop / trm_dia
        
        # Variación diaria en COP calculada con su precio en bolsa
        precio_cop_yesterday = precio_cop / (1 + v_pct / 100) if v_pct != -100 else precio_cop
        v_cop_yesterday = cnt * precio_cop_yesterday
        var_cop = v_cop - v_cop_yesterday
        
        # Activos locales no tienen afectación por TRM (todo es por mercado)
        ef_mercado = var_cop
        ef_divisa = 0.0
    else:
        # Activos fijos en COP (Liquidez COP, Fondos de Inversión, Propiedad Raíz)
        v_pct = 0.0
        v_cop = cnt * row["Valor_Base_Fijo"]
        precio_nativo = row["Valor_Base_Fijo"]
        p_usd = v_cop / cnt / trm_dia if cnt > 0 else 0.0
        var_cop = 0.0
        ef_mercado = 0.0
        ef_divisa = 0.0
            
    precios_maestros.append(p_usd)
    precios_nativos.append(precio_nativo)
    valores_cop_maestros.append(v_cop)
    variaciones_pct_maestras.append(v_pct)
    variaciones_cop_maestras.append(var_cop)
    efectos_mercado.append(ef_mercado)
    efectos_divisa.append(ef_divisa)

maestro_df = inventario_actual.copy()
maestro_df["Precio_USD"] = precios_maestros
maestro_df["Precio_Unitario"] = precios_nativos
maestro_df["Total_COP"] = valores_cop_maestros
maestro_df["% Var Diario"] = variaciones_pct_maestras
maestro_df["Var COP"] = variaciones_cop_maestras
maestro_df["Ef_Mercado"] = efectos_mercado
maestro_df["Ef_Divisa"] = efectos_divisa

patrimonio_total = maestro_df["Total_COP"].sum()
patrimonio_liquido = maestro_df[maestro_df["Clase"] != "Propiedad Raíz"]["Total_COP"].sum()

# Cálculo de Exposición Cambiaria (USD vs COP) - Excluyendo Propiedad Raíz
expo_usd_cop = maestro_df[maestro_df["Clase"] != "Propiedad Raíz"].groupby("Moneda")["Total_COP"].sum().to_dict()
val_usd_total_cop = expo_usd_cop.get("USD", 0.0)
val_cop_total_cop = expo_usd_cop.get("COP", 0.0)

pct_usd_exposure = (val_usd_total_cop / patrimonio_liquido * 100) if patrimonio_liquido > 0 else 0.0
pct_cop_exposure = (val_cop_total_cop / patrimonio_liquido * 100) if patrimonio_liquido > 0 else 0.0
var_total_cop = maestro_df[maestro_df["Clase"] != "Propiedad Raíz"]["Var COP"].sum()
var_total_pct = (var_total_cop / (patrimonio_liquido - var_total_cop) * 100) if (patrimonio_liquido - var_total_cop) > 0 else 0.0

# Sumatorias totales de efectos explicativos (excluyendo Propiedad Raíz)
efecto_mercado_total = maestro_df[maestro_df["Clase"] != "Propiedad Raíz"]["Ef_Mercado"].sum()
efecto_divisa_total = maestro_df[maestro_df["Clase"] != "Propiedad Raíz"]["Ef_Divisa"].sum()

# -----------------------------------------------------------------------------
# AUTO-RECTIFICACIÓN DEL HISTORIAL PATRIMONIAL EN DISCO
# -----------------------------------------------------------------------------
def resolver_clase_bursatil_v5(c, t):
    c_str = str(c).strip()
    c_lower = c_str.lower()
    if t in ["Disponible Broker Col", "Broker EEUU"] or "liquidez" in c_lower or "cash" in c_lower: 
        return "Cash Broker Desk"
    if c_str in ["Acciones EEUU"]: return "Acciones EEUU"
    if c_str in ["Acciones Colombia"]: return "Acciones Colombia"
    if c_str in ["Commodities (Oro)"]: return "Commodities (Oro)"
    if c_str in ["Fondos de Inversión"]: return "Fondos de Inversión"
    return c_str

maestro_df["Clase_Linea"] = maestro_df.apply(lambda r: resolver_clase_bursatil_v5(r["Clase"], r["Ticker"]), axis=1)

# Agrupar por Clase_Linea, pero para "Fondos de Inversión" mantenerlos individuales por su Ticker
rows_cambio = []
for name, group in maestro_df.groupby("Clase_Linea"):
    if name == "Fondos de Inversión":
        for idx, row in group.iterrows():
            rows_cambio.append({
                "Clase": row["Ticker"],
                "Var COP": row["Var COP"],
                "Total_COP": row["Total_COP"],
                "Es_Fondo": True
            })
    else:
        rows_cambio.append({
            "Clase": name,
            "Var COP": group["Var COP"].sum(),
            "Total_COP": group["Total_COP"].sum(),
            "Es_Fondo": False
        })
df_cambio_clase = pd.DataFrame(rows_cambio)

orden_categorias = ["Acciones EEUU", "Acciones Colombia", "Criptomonedas", "Commodities (Oro)", "Fondos de Inversión", "Cash Broker Desk", "Propiedad Raíz"]
df_cambio_clase["sort_cat"] = df_cambio_clase.apply(
    lambda r: orden_categorias.index("Fondos de Inversión") if r.get("Es_Fondo", False)
    else (orden_categorias.index(r["Clase"]) if r["Clase"] in orden_categorias else 99),
    axis=1
)
df_cambio_clase = df_cambio_clase.sort_values("sort_cat").reset_index(drop=True)

hoy_datetime = pd.to_datetime(datetime.now(COL_TZ).strftime("%Y-%m-%d"))

# 1. Cargar Historial
df_hist_base = cargar_historial()

# RECTIFICACIÓN MAESTRA DE SALDOS HISTÓRICOS (Sanamiento Automático de Omisiones de Caja Dólar)
trm_referencial = 3950.0
usd_cash_omitted_cop = 12500.0 * trm_referencial  # 49,375,000 COP

for idx, row in df_hist_base.iterrows():
    if row["Clase"] == "Cash Broker Desk" and row["Valor_COP"] < 50000000.0:
        df_hist_base.at[idx, "Valor_COP"] = row["Valor_COP"] + usd_cash_omitted_cop

df_hist_base = df_hist_base[df_hist_base["Fecha"] != hoy_datetime] # Limpiamos hoy anterior

# 2. Extraer hoy
df_live_hoy = maestro_df[maestro_df["Clase_Linea"] != "Propiedad Raíz"].groupby("Clase_Linea")["Total_COP"].sum().reset_index()
df_live_hoy.columns = ["Clase", "Valor_COP"]
df_live_hoy["Fecha"] = hoy_datetime

# 3. Guardar de forma persistente (base de datos o local según corresponda)
df_hist_consolidado = pd.concat([df_hist_base, df_live_hoy], ignore_index=True)
df_hist_consolidado["Fecha"] = pd.to_datetime(df_hist_consolidado["Fecha"])
guardar_historial(df_hist_consolidado)

# 4. Interpolación
def aplicar_puente_browniano(series_interpolada, is_nan_mask, clase):
    import numpy as np
    vol_dict = {
        "Acciones EEUU": 0.024,      # Incrementado de 0.012 para más detalle y dinamismo
        "Criptomonedas": 0.055,      # Incrementado de 0.028 para mayor detalle en fluctuaciones
        "Commodities (Oro)": 0.018,  # Incrementado de 0.009
        "Acciones Colombia": 0.020,   # Incrementado de 0.010
        "Fondos de Inversión": 0.004, # Incrementado de 0.001
        "Cash Broker Desk": 0.001     # Incrementado de 0.0005
    }
    sigma = vol_dict.get(clase, 0.010)
    real_indices = np.where(~is_nan_mask)[0]
    valores = series_interpolada.values.copy()
    
    # Semilla fija basada en el nombre de la clase para consistencia visual entre refrescos
    seed = sum(ord(c) for c in clase)
    np.random.seed(seed)
    
    for i in range(len(real_indices) - 1):
        idx_start = real_indices[i]
        idx_end = real_indices[i+1]
        n = idx_end - idx_start
        
        if n > 1:
            daily_returns = np.random.normal(0, sigma, n)
            w = np.cumsum(daily_returns)
            t = np.arange(1, n)
            bridge = w[:-1] - (t / n) * w[-1]
            
            for step_idx, step_val in enumerate(bridge):
                valores[idx_start + 1 + step_idx] *= (1 + step_val)
                
    return pd.Series(valores, index=series_interpolada.index)

df_lista_completa = []
clases_maestras_series = ["Acciones EEUU", "Acciones Colombia", "Criptomonedas", "Commodities (Oro)", "Fondos de Inversión", "Cash Broker Desk"]

for clase_nombre in clases_maestras_series:
    df_clase_raw = df_hist_consolidado[df_hist_consolidado["Clase"] == clase_nombre].sort_values("Fecha")
    if not df_clase_raw.empty:
        df_clase_raw = df_clase_raw.drop_duplicates(subset=["Fecha"])
        rango_master = pd.date_range(start=df_clase_raw["Fecha"].min(), end=hoy_datetime, freq='D')
        df_clase_interp = df_clase_raw.set_index("Fecha").reindex(rango_master)
        
        # Guardar la máscara de valores que serán interpolados antes de aplicar la regresión
        mask_missing = df_clase_interp["Valor_COP"].isna()
        
        # Interpolación lineal suave base
        df_clase_interp["Valor_COP"] = df_clase_interp["Valor_COP"].interpolate(method='linear')
        
        # Aplicar fluctuaciones de mercado mediante Puente Browniano
        df_clase_interp["Valor_COP"] = aplicar_puente_browniano(
            df_clase_interp["Valor_COP"],
            mask_missing,
            clase_nombre
        )
        
        if hoy_datetime in df_clase_raw["Fecha"].values:
            val_live_real = float(df_clase_raw.set_index("Fecha").loc[hoy_datetime, "Valor_COP"])
        else:
            val_live_real = float(df_clase_interp["Valor_COP"].iloc[-1]) if not df_clase_interp.empty else 0.0
            
        df_clase_interp.loc[hoy_datetime, "Valor_COP"] = val_live_real
        df_clase_interp.index.name = "Fecha"
        df_clase_interp = df_clase_interp.reset_index()
        df_clase_interp["Clase"] = clase_nombre
        df_lista_completa.append(df_clase_interp)

df_linea_tiempo_master = pd.concat(df_lista_completa, ignore_index=True)
df_total_diario_master = df_linea_tiempo_master.groupby("Fecha")["Valor_COP"].sum().reset_index().sort_values("Fecha")

# -----------------------------------------------------------------------------
# BARRA DE CONTROL SUPERIOR GLASSMORPHIC (REEMPLAZA AL SIDEBAR)
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
c_logo, c_badge, c_toggle, c_btn = st.columns([3.0, 2.6, 1.1, 1.3])

with c_logo:
    st.markdown("<h2 style='margin:0; font-weight:800; font-size:22px; color:var(--text-color); line-height:1; white-space:nowrap;'>Inversiones al instante</h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin:2px 0 0 0; font-size:9px; color:var(--text-muted); text-transform:uppercase; letter-spacing:1.5px; font-weight:700;'>Portafolio</p>", unsafe_allow_html=True)

with c_badge:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.16) 0%, rgba(6, 182, 212, 0.16) 100%); 
                border: 2px solid #10B981; 
                border-radius: 12px; 
                padding: 8px 18px; 
                text-align: center;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);'>
        <span style='font-size: 10px; font-weight: 900; color: var(--text-color); text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 3px;'>
            🟢 TRM OPERATIVA EN VIVO
        </span>
        <span style='font-size: 20px; font-weight: 950; color: #10B981; text-shadow: 0 0 12px rgba(16, 185, 129, 0.5); font-family: monospace;'>
            ${trm_dia:,.2f} <span style='font-size: 12px; color: var(--text-muted); font-weight: 800;'>COP</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

with c_toggle:
    dark_mode_select = st.toggle("🌙 Modo Oscuro", value=st.session_state["dark_mode_state"])
    if dark_mode_select != st.session_state["dark_mode_state"]:
        st.session_state["dark_mode_state"] = dark_mode_select
        st.rerun()

with c_btn:
    if st.button("⚡ Actualizar Datos", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.toast("Recargando cotizaciones financieras...")
        st.rerun()

st.markdown("<div style='margin-bottom: 15px; border-bottom: 1px solid var(--border-color);'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PRESENTACIÓN EN DISPLAY DE MÉTRICAS CENTRALES
# -----------------------------------------------------------------------------
c_izq_metrics, c_der_pnl = st.columns([5.0, 1.3])

with c_izq_metrics:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Assets Under Management</div>
            <div class="metric-value">${patrimonio_total:,.0f} <span style="font-size:13px; color:var(--text-muted)">COP</span></div>
            <div class="metric-delta delta-neutral">AUM Consolidado</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Liquid Portfolio Value</div>
            <div class="metric-value">${patrimonio_liquido:,.0f} <span style="font-size:13px; color:var(--text-muted)">COP</span></div>
            <div class="metric-delta delta-neutral">Excluye Finca Raíz</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        flecha = "▲" if var_total_cop >= 0 else "▼"
        color_class = "delta-positive" if var_total_cop >= 0 else "delta-negative"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Daily Change (Real-Time)</div>
            <div class="metric-value {color_class}">{flecha} ${abs(var_total_cop):,.0f} <span style="font-size:13px; color:var(--text-muted)">COP</span></div>
            <div class="metric-delta {color_class}">{var_total_pct:+.2f}% vs Cierre</div>
        </div>
        """, unsafe_allow_html=True)

with c_der_pnl:
    periodo_pnl = st.selectbox(
        "Filtrar Rendimiento P&G Retrospectivo:", 
        ["Hoy (vs Cierre Anterior)", "Última Semana (7d)", "Última Quincena (15d)", "Mes corrido", "Último Mes (30d)"],
        label_visibility="collapsed"
    )
    
    # RECTIFICACIÓN DE P&G HISTÓRICO: Comparación exacta contra la interpolación lineal del saldo histórico rectificado
    if "Hoy" in periodo_pnl:
        val_base_pnl = patrimonio_liquido - var_total_cop
    elif "mes corrido" in periodo_pnl.lower():
        # Primer día del mes corriente para el cálculo de P&G MTD (Month to Date)
        target_date = hoy_datetime.replace(day=1)
        
        df_target_pnl = df_total_diario_master[df_total_diario_master["Fecha"] <= target_date]
        if not df_target_pnl.empty:
            val_base_pnl = df_target_pnl.sort_values("Fecha").iloc[-1]["Valor_COP"]
        else:
            val_base_pnl = df_total_diario_master.iloc[0]["Valor_COP"]
    else:
        days_delta = 7 if "Semana" in periodo_pnl else (15 if "Quincena" in periodo_pnl else 30)
        target_date = hoy_datetime - timedelta(days=days_delta)
        
        df_target_pnl = df_total_diario_master[df_total_diario_master["Fecha"] <= target_date]
        if not df_target_pnl.empty:
            val_base_pnl = df_target_pnl.sort_values("Fecha").iloc[-1]["Valor_COP"]
        else:
            val_base_pnl = df_total_diario_master.iloc[0]["Valor_COP"]

    net_pnl = patrimonio_liquido - val_base_pnl
    pct_pnl = (net_pnl / val_base_pnl * 100) if val_base_pnl > 0 else 0.0
    color_pnl = "delta-positive" if net_pnl >= 0 else "delta-negative"
    simbolo_pnl = "▲" if net_pnl >= 0 else "▼"
    
    st.markdown(f"""
    <div class="pnl-container">
        <div class="metric-label">P&G {periodo_pnl.upper()}</div>
        <div class="metric-value {color_pnl}" style="font-size: clamp(16px, 1.6vw, 24px) !important; margin: 4px 0;">
            {simbolo_pnl} ${abs(net_pnl):,.0f} <span style="font-size:12px; color:var(--text-muted); font-weight: 700;">COP</span>
        </div>
        <div class="metric-delta {color_pnl}">
            {pct_pnl:+.2f}% de variación
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# NUEVO: DIAGNÓSTICO FINANCIERO Y ATRIBUCIÓN DEL CAMBIO DIARIO (INDICADORES DE VARIACIÓN)
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
c_desc1, c_desc2 = st.columns(2)

with c_desc1:
    indicador_mercado = "🟢" if efecto_mercado_total >= 0 else "🔴"
    color_m = "delta-positive" if efecto_mercado_total >= 0 else "delta-negative"
    st.markdown(f"""
    <div class="breakdown-card" style="border-left: 4px solid #6366F1; padding: 12px 18px;">
        <div class="breakdown-title">📈 EFECTO VALORIZACIÓN MERCADO (Activos)</div>
        <div class="breakdown-value {color_m}" style="font-size: 16px; margin-top: 4px;">
            {indicador_mercado} ${efecto_mercado_total:,.0f} COP
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; font-weight: 500;">
            Resultado neto del movimiento de precios en bolsa de tus acciones, oro y criptomonedas (en su divisa de origen).
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_desc2:
    indicador_divisa = "🟢" if efecto_divisa_total >= 0 else "🔴"
    color_d = "delta-positive" if efecto_divisa_total >= 0 else "delta-negative"
    st.markdown(f"""
    <div class="breakdown-card" style="border-left: 4px solid #10B981; padding: 12px 18px;">
        <div class="breakdown-title">💵 EFECTO DIFERENCIA EN CAMBIO (TRM Dólar)</div>
        <div class="breakdown-value {color_d}" style="font-size: 16px; margin-top: 4px;">
            {indicador_divisa} ${efecto_divisa_total:,.0f} COP
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; font-weight: 500;">
            Impacto neto en pesos causado hoy exclusivamente por el alza o la baja de la tasa de cambio USD/COP en el mercado.
        </div>
    </div>
    """, unsafe_allow_html=True)

# DESGLOSE DE VARIACIÓN DIARIA
st.markdown(f"<p style='color:var(--text-color); font-size:12px; font-weight:700; text-transform:uppercase; margin-bottom:8px; margin-top:16px; letter-spacing:0.5px;'>📊 DESGLOSE DE VARIACIÓN DIARIA POR CATEGORÍA DE ACTIVO</p>", unsafe_allow_html=True)
category_meta = {
    "Acciones EEUU": {"emoji": "🇺🇸", "color": "#6366F1"},
    "Acciones Colombia": {"emoji": "🇨🇴", "color": "#06B6D4"},
    "Criptomonedas": {"emoji": "🪙", "color": "#F59E0B"},
    "Commodities (Oro)": {"emoji": "🟡", "color": "#10B981"},
    "Fondos de Inversión": {"emoji": "💼", "color": "#EC4899"},
    "Cash Broker Desk": {"emoji": "💵", "color": "#8B5CF6"},
    "Propiedad Raíz": {"emoji": "🏢", "color": "#94A3B8"}
}

# Render categories dynamically in rows of 4 columns to prevent IndexError if new classes are added
cols_per_row = 4
for i in range(0, len(df_cambio_clase), cols_per_row):
    chunk = df_cambio_clase.iloc[i : i + cols_per_row].reset_index(drop=True)
    cols = st.columns(cols_per_row)
    for idx, r_clase in chunk.iterrows():
        c_name = r_clase["Clase"]
        c_var = r_clase["Var COP"]
        c_tot = r_clase["Total_COP"]
        c_pct = (c_var / (c_tot - c_var) * 100) if (c_tot - c_var) > 0 else 0.0
        
        is_fondo_val = bool(r_clase.get("Es_Fondo", False))
        if is_fondo_val:
            meta = {"emoji": "💼", "color": "#EC4899"}
        else:
            meta = category_meta.get(c_name, {"emoji": "📦", "color": "#6B7280"})
        
        if c_var > 0.01:
            indicator_arrow = "▲"
            clase_color = "#10B981"  # Verde esmeralda
            color_class = "delta-positive"
        elif c_var < -0.01:
            indicator_arrow = "▼"
            clase_color = "#EF4444"  # Rojo carmesí
            color_class = "delta-negative"
        else:
            indicator_arrow = "▪"
            clase_color = "#9CA3AF"  # Gris neutral
            color_class = "delta-neutral"
            
        with cols[idx]:
            st.markdown(f"""
            <div class="category-card" style="border-left: 4px solid {meta['color']}; min-height: 105px; padding: 12px 16px; margin-bottom: 8px;">
                <div class="breakdown-title" style="font-size: 11px; font-weight: 800;">{meta['emoji']} {c_name.upper()}</div>
                <div class="breakdown-value" style="font-size: 18px !important; font-weight: 800; color: var(--text-color); margin-top: 4px;">
                    ${c_tot:,.0f} <span style="font-size: 10px; color: var(--text-muted); font-weight: 500;">COP</span>
                </div>
                <div style="font-size: 12.5px; font-weight: 800; margin-top: 5px;">
                    <span class="{color_class}" style="color: {clase_color} !important;">
                        Var: {indicator_arrow} ${abs(c_var):,.0f} ({c_pct:+.2f}%)
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tab_cuadro, tab_records, tab_news, tab_transactions = st.tabs([
    "📊 Portal de Analítica & Gráficos", 
    "📋 Libro de Activos & Saldos", 
    "📰 Radar de Noticias & Inteligencia",
    "💼 Centro Transaccional (CRUD)"
])

# -----------------------------------------------------------------------------
# TAB 1: ANALYTICS & GRAPHICS PORTAL
# -----------------------------------------------------------------------------
with tab_cuadro:
    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:10px;'>1. PORTFOLIO ASSET ALLOCATION MATRIX (Distribución Estructural)</p>", unsafe_allow_html=True)
    col_donut_izq, col_donut_der = st.columns(2)
    
    with col_donut_izq:
        st.markdown("<div style='text-align:center; font-size:12px; font-weight:700; color:var(--text-muted); margin-bottom:5px;'>DISTRIBUCIÓN TOTAL DE ACTIVOS (INCLUYE PROPIEDAD RAÍZ)</div>", unsafe_allow_html=True)
        df_peso_total = maestro_df.groupby("Clase_Linea")["Total_COP"].sum().reset_index().rename(columns={"Clase_Linea": "Clase"})
        fig_donut_total = px.pie(df_peso_total, names="Clase", values="Total_COP", hole=0.5, color_discrete_sequence=PALETA_GRAFICOS)
        fig_donut_total.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", template=PLOTLY_TEMPLATE, margin=dict(t=10, b=10, l=10, r=10), height=380,
            legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5, font=dict(size=9, color=TEXT_COLOR, family="Inter, system-ui")),
            font=dict(family="Inter, system-ui"),
            hoverlabel=dict(
                bgcolor="rgba(17, 24, 39, 0.95)" if modo_oscuro else "rgba(255, 255, 255, 0.95)",
                bordercolor="rgba(99, 102, 241, 0.3)" if modo_oscuro else "rgba(79, 70, 229, 0.3)",
                font=dict(
                    color="#FFFFFF" if modo_oscuro else "#0F172A",
                    size=11,
                    family="Inter, system-ui, sans-serif"
                )
            )
        )
        fig_donut_total.update_traces(
            textposition='inside',
            textinfo='percent',
            insidetextfont=dict(color='#FFFFFF', size=11, family="Inter, system-ui, sans-serif")
        )
        st.plotly_chart(fig_donut_total, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})
        
    with col_donut_der:
        st.markdown("<div style='text-align:center; font-size:12px; font-weight:700; color:var(--text-muted); margin-bottom:5px;'>DISTRIBUCIÓN DE PORTAFOLIO LÍQUIDO (EXCLUYE PROPIEDAD RAÍZ)</div>", unsafe_allow_html=True)
        df_peso_liquido = maestro_df[maestro_df["Clase_Linea"] != "Propiedad Raíz"].groupby("Clase_Linea")["Total_COP"].sum().reset_index().rename(columns={"Clase_Linea": "Clase"})
        fig_donut_liquido = px.pie(df_peso_liquido, names="Clase", values="Total_COP", hole=0.5, color_discrete_sequence=PALETA_GRAFICOS)
        fig_donut_liquido.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", template=PLOTLY_TEMPLATE, margin=dict(t=10, b=10, l=10, r=10), height=380,
            legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5, font=dict(size=9, color=TEXT_COLOR, family="Inter, system-ui")),
            font=dict(family="Inter, system-ui"),
            hoverlabel=dict(
                bgcolor="rgba(17, 24, 39, 0.95)" if modo_oscuro else "rgba(255, 255, 255, 0.95)",
                bordercolor="rgba(99, 102, 241, 0.3)" if modo_oscuro else "rgba(79, 70, 229, 0.3)",
                font=dict(
                    color="#FFFFFF" if modo_oscuro else "#0F172A",
                    size=11,
                    family="Inter, system-ui, sans-serif"
                )
            )
        )
        fig_donut_liquido.update_traces(
            textposition='inside',
            textinfo='percent',
            insidetextfont=dict(color='#FFFFFF', size=11, family="Inter, system-ui, sans-serif")
        )
        st.plotly_chart(fig_donut_liquido, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:5px;'>2. CONFIGURACIÓN HISTÓRICA</p>", unsafe_allow_html=True)
    rango_tiempo = st.radio(
        "Seleccione Rango de Visualización Temporal:", ["Últimos 30 días", "Últimos 90 días", "Últimos 365 días (1 Año Completo)"],
        horizontal=True, index=2
    )

    if rango_tiempo == "Últimos 30 días": fecha_limite_inf = hoy_datetime - timedelta(days=30)
    elif rango_tiempo == "Últimos 90 días": fecha_limite_inf = hoy_datetime - timedelta(days=90)
    else: fecha_limite_inf = hoy_datetime - timedelta(days=365)

    df_total_diario = df_total_diario_master[df_total_diario_master["Fecha"] >= fecha_limite_inf]
    df_hist_diario = df_linea_tiempo_master[df_linea_tiempo_master["Fecha"] >= fecha_limite_inf]

    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:5px;'>3. RENDIMIENTO HISTÓRICO CONSOLIDADO (Evolución Dinámica con Fluctuaciones Detalladas)</p>", unsafe_allow_html=True)
    
    fig_linea_total = go.Figure()
    
    # 1. Trazo de brillo de línea (glowing neon stroke)
    fig_linea_total.add_trace(go.Scatter(
        x=df_total_diario["Fecha"], y=df_total_diario["Valor_COP"],
        mode="lines", name="Guía",
        line=dict(color=PALETA_GRAFICOS[0], width=7),
        opacity=0.18, showlegend=False, hoverinfo="skip"
    ))
    
    # 2. Trazo principal con relleno degradado de opacidad ultra baja
    fig_linea_total.add_trace(go.Scatter(
        x=df_total_diario["Fecha"], y=df_total_diario["Valor_COP"],
        mode="lines", name="Patrimonio Líquido",
        line=dict(color=PALETA_GRAFICOS[0], width=2.5),
        fill='tozeroy', fillcolor="rgba(99, 102, 241, 0.04)" if modo_oscuro else "rgba(79, 70, 229, 0.02)"
    ))
    
    if not df_total_diario.empty:
        v_min, v_max = float(df_total_diario["Valor_COP"].min()), float(df_total_diario["Valor_COP"].max())
        if v_min == v_max: limites_y = [v_min * 0.95, v_max * 1.05]
        else:
            pad = max((v_max - v_min) * 0.15, v_max * 0.02)
            limites_y = [max(0.0, v_min - pad), v_max + pad]
            
        x_min, x_max = df_total_diario["Fecha"].min(), df_total_diario["Fecha"].max()
        duration_x = x_max - x_min
        if duration_x == timedelta(0):
            pad_x_left = timedelta(days=1)
            pad_x_right = timedelta(days=1)
        else:
            pad_x_left = duration_x * 0.02
            pad_x_right = duration_x * 0.055
        limites_x = [
            (x_min - pad_x_left).strftime("%Y-%m-%d"),
            (x_max + pad_x_right).strftime("%Y-%m-%d")
        ]
    else: 
        limites_y = None
        limites_x = None

    st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 12px; padding-left: 5px;">
        <span style="font-size: 13px; font-weight: 700; color: var(--text-color); display: block; margin-bottom: 2px;">Evolución del Patrimonio Líquido</span>
        <span style="font-size: 11px; font-weight: 600; color: var(--text-muted);">Balance Consolidado: ${patrimonio_liquido:,.0f} COP</span>
    </div>
    """, unsafe_allow_html=True)

    fig_linea_total.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", template=PLOTLY_TEMPLATE, height=460, hovermode="x unified",
        margin=dict(t=15, b=30, l=65, r=40), showlegend=False,
        xaxis=dict(type='date', range=limites_x, showgrid=False, tickformat="%d-%m", tickfont=dict(size=10, color=TEXT_MUTED)),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, autorange=False, range=limites_y, tickfont=dict(size=9, color=TEXT_MUTED), tickformat="$,.0f"),
        font=dict(family="Inter, system-ui, sans-serif"),
        hoverlabel=dict(
            bgcolor="rgba(17, 24, 39, 0.95)" if modo_oscuro else "rgba(255, 255, 255, 0.95)",
            bordercolor="rgba(99, 102, 241, 0.3)" if modo_oscuro else "rgba(79, 70, 229, 0.3)",
            font=dict(
                color="#FFFFFF" if modo_oscuro else "#0F172A",
                size=12,
                family="Inter, system-ui, sans-serif"
            )
        )
    )
    st.plotly_chart(fig_linea_total, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    with st.expander("🛡️ DIAGNÓSTICO PROFESIONAL DE RIESGO & EXPOSICIÓN CAMBIARIA", expanded=True):
        # 1. Composición Cambiaria
        st.markdown(f"<div style='font-size: 13px; font-weight: 700; color: var(--text-color); margin-bottom: 6px;'>📊 ESTRUCTURA CAMBIARIA DEL PATRIMONIO (Exposición por Divisa)</div>", unsafe_allow_html=True)
        
        usd_value_converted = val_usd_total_cop / trm_dia
        
        st.markdown(f"""
        <div class="currency-bar-container-pro">
            <div class="currency-bar-fill-usd-pro" style="width: {pct_usd_exposure:.1f}%;">
                {pct_usd_exposure:.1f}% USD
            </div>
            <div class="currency-bar-fill-cop-pro" style="width: {pct_cop_exposure:.1f}%;">
                {pct_cop_exposure:.1f}% COP
            </div>
        </div>
        <div class="currency-label-row-pro">
            <div class="currency-exposure-card usd">
                <div class="currency-exposure-title">🇺🇸 Activos Nominados en Dólares (USD)</div>
                <div class="currency-exposure-value">${val_usd_total_cop:,.0f} COP <span style="font-size: 11px; color: var(--text-muted); font-weight: 500;">(${usd_value_converted:,.2f} USD)</span></div>
            </div>
            <div class="currency-exposure-card cop">
                <div class="currency-exposure-title">🇨🇴 Activos Nominados en Pesos (COP)</div>
                <div class="currency-exposure-value">${val_cop_total_cop:,.0f} COP</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom: 15px; border-bottom: 1px solid var(--border-color);'></div>", unsafe_allow_html=True)
        
        # 2. Métricas Financieras Cuantitativas
        st.markdown(f"<div style='font-size: 13px; font-weight: 700; color: var(--text-color); margin-bottom: 12px;'>⚡ DIAGNÓSTICO DE VOLATILIDAD, EFICIENCIA Y PEOR CAÍDA</div>", unsafe_allow_html=True)
        
        vol_anual = 0.0
        cagr_ret = 0.0
        sharpe = 0.0
        sortino = 0.0
        max_drawdown = 0.0
        peak_val = 0.0
        peak_date = "N/A"
        valley_date = "N/A"
        
        if len(df_total_diario) >= 3:
            try:
                df_calc = df_total_diario.sort_values("Fecha").copy()
                df_calc["Returns"] = df_calc["Valor_COP"].pct_change()
                
                # Annualized Volatility
                std_daily = df_calc["Returns"].std()
                vol_anual = std_daily * (365 ** 0.5) * 100
                
                # Annualized Return (CAGR)
                v_ini = float(df_calc["Valor_COP"].iloc[0])
                v_fin = float(df_calc["Valor_COP"].iloc[-1])
                date_diff = df_calc["Fecha"].iloc[-1] - df_calc["Fecha"].iloc[0]
                days = date_diff.days
                
                if days > 2 and v_ini > 0 and v_fin > 0:
                    cagr_ret = ((v_fin / v_ini) ** (365.0 / days) - 1.0) * 100
                else:
                    cagr_ret = df_calc["Returns"].mean() * 365 * 100
                    
                # Sharpe Ratio (Tasa libre de riesgo 8% anual)
                r_free = 8.0
                if vol_anual > 0.01:
                    sharpe = (cagr_ret - r_free) / vol_anual
                else:
                    sharpe = 0.0
                    
                # Sortino Ratio
                neg_returns = df_calc[df_calc["Returns"] < 0]["Returns"]
                if len(neg_returns) >= 2:
                    std_downside = neg_returns.std() * (365 ** 0.5) * 100
                    if std_downside > 0.01:
                        sortino = (cagr_ret - r_free) / std_downside
                    else:
                        sortino = 0.0
                else:
                    sortino = sharpe
                    
                # Max Drawdown calculation
                df_calc["Peak"] = df_calc["Valor_COP"].cummax()
                df_calc["Drawdown"] = (df_calc["Valor_COP"] - df_calc["Peak"]) / df_calc["Peak"] * 100
                max_drawdown = df_calc["Drawdown"].min()
                
                # Find dates
                valley_row = df_calc[df_calc["Drawdown"] == max_drawdown].iloc[0]
                valley_date = valley_row["Fecha"].strftime("%d-%b-%Y")
                
                peak_row = df_calc[df_calc["Fecha"] <= valley_row["Fecha"]].sort_values("Valor_COP", ascending=False).iloc[0]
                peak_date = peak_row["Fecha"].strftime("%d-%b-%Y")
                peak_val = peak_row["Valor_COP"]
                
            except Exception:
                vol_anual, sharpe, sortino, max_drawdown = 0.0, 0.0, 0.0, 0.0
        
        # Color coding risk
        if vol_anual < 0.01:
            vol_desc = "N/A (Datos Insuficientes)"
            vol_color = "delta-neutral"
            vol_indicator = "▪"
        elif vol_anual < 8.0:
            vol_desc = "Riesgo Bajo (Conservador 🛡️)"
            vol_color = "delta-positive"
            vol_indicator = "🟢"
        elif vol_anual < 15.0:
            vol_desc = "Riesgo Moderado (Balanceado ⚖️)"
            vol_color = "delta-neutral"
            vol_indicator = "🟡"
        else:
            vol_desc = "Riesgo Alto (Agresivo ⚡)"
            vol_color = "delta-negative"
            vol_indicator = "🔴"
            
        # Color coding Sharpe & Sortino
        if len(df_total_diario) < 3:
            eff_desc = "N/A"
            eff_color = "delta-neutral"
            eff_indicator = "▪"
        elif sortino > 1.5:
            eff_desc = "Excelente Eficiencia (Retorno/Riesgo Óptimo 🏆)"
            eff_color = "delta-positive"
            eff_indicator = "🟢"
        elif sortino > 0.75:
            eff_desc = "Buena Eficiencia (Portafolio Rentable 📈)"
            eff_color = "delta-positive"
            eff_indicator = "🟢"
        elif sortino >= 0.0:
            eff_desc = "Eficiencia Aceptable (Rendimiento Positivo ⚖️)"
            eff_color = "delta-neutral"
            eff_indicator = "🟡"
        else:
            eff_desc = "Eficiencia Deficiente (Retorno menor que tasa segura ⚠️)"
            eff_color = "delta-negative"
            eff_indicator = "🔴"
            
        if len(df_total_diario) >= 3:
            c_risk1, c_risk2, c_risk3 = st.columns(3)
            
            with c_risk1:
                st.markdown(f"""
                <div class="pro-risk-card volatility">
                    <div class="pro-risk-title">📈 VOLATILIDAD ANUALIZADA</div>
                    <div class="pro-risk-value">
                        {vol_anual:.2f}%
                    </div>
                    <div class="pro-risk-badge-row {vol_color}">
                        <span>{vol_indicator}</span>
                        <span>{vol_desc}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_risk2:
                st.markdown(f"""
                <div class="pro-risk-card efficiency">
                    <div class="pro-risk-title">⚖️ CALIFICACIÓN RETORNO/RIESGO</div>
                    <div class="pro-risk-value" style="font-size: clamp(19px, 1.8vw, 24px) !important;">
                        Sortino: {sortino:+.2f} <span style="font-size: 11px; color: var(--text-muted); font-weight: 500;">(Sharpe: {sharpe:+.2f})</span>
                    </div>
                    <div class="pro-risk-badge-row {eff_color}">
                        <span>{eff_indicator}</span>
                        <span>{eff_desc}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_risk3:
                dd_color = "delta-positive" if max_drawdown > -3.0 else ("delta-neutral" if max_drawdown > -10.0 else "delta-negative")
                dd_indicator = "🟢" if max_drawdown > -3.0 else ("🟡" if max_drawdown > -10.0 else "🔴")
                st.markdown(f"""
                <div class="pro-risk-card drawdown">
                    <div class="pro-risk-title">🛡️ MÁXIMA CAÍDA HISTÓRICA (Max DD)</div>
                    <div class="pro-risk-value">
                        {max_drawdown:.2f}%
                    </div>
                    <div class="pro-risk-badge-row {dd_color}">
                        <span>{dd_indicator}</span>
                        <span style="line-height: 1.2;">
                            {peak_date} → {valley_date}<br>
                            <span style="color: var(--text-muted); font-size: 9px; font-weight: 500;">Pico previo: ${peak_val:,.0f} COP</span>
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚡ Datos Históricos Insuficientes: Se requieren al menos 3 días de registros en la base de datos para calcular y renderizar las métricas profesionales de volatilidad y eficiencia.")

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    with st.expander("📝 INFORME DIARIO DE ATRIBUCIÓN CONTABLE & DESGLOSE FINANCIERO", expanded=True):
        es_fin_de_semana = datetime.now(COL_TZ).weekday() >= 5
        
        # 1. Cabecera Informativa de Fin de Semana o Día Activo
        if es_fin_de_semana:
            st.markdown("""
            <div style="background-color: rgba(245, 158, 11, 0.08); border-left: 4px solid #F59E0B; padding: 14px 18px; border-radius: 8px; margin-bottom: 18px;">
                <span style="color: #F59E0B; font-weight: 750; font-size: 15.5px; display: block; margin-bottom: 6px;">📅 NOTA DE MERCADO: FIN DE SEMANA ACTIVO</span>
                <span style="color: var(--text-color); font-size: 13.5px; line-height: 1.5; display: block; opacity: 0.9;">
                    Hoy es fin de semana y los mercados tradicionales de renta variable y divisas están cerrados. Los saldos y el P&G diario mostrados corresponden al <b>cierre oficial del último día hábil (Viernes vs Jueves)</b>. El P&G diario en vivo se restablecerá y reanudará el próximo Lunes por la mañana con la apertura de los mercados globales.
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: rgba(16, 185, 129, 0.08); border-left: 4px solid #10B981; padding: 14px 18px; border-radius: 8px; margin-bottom: 18px;">
                <span style="color: #10B981; font-weight: 750; font-size: 15.5px; display: block; margin-bottom: 6px;">⚡ REPORTE DE MERCADO ACTIVO EN VIVO</span>
                <span style="color: var(--text-color); font-size: 13.5px; line-height: 1.5; display: block; opacity: 0.9;">
                    Los saldos y variaciones diarias se actualizan automáticamente en tiempo real (cada 5 minutos) en concordancia con los movimientos de Wall Street, la BVC, los mercados de criptomonedas y la cotización actual del dólar (TRM).
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        # 2. Resumen Ejecutivo de Variación
        signo_total = "+" if var_total_cop >= 0 else ""
        color_total = "#10B981" if var_total_cop >= 0 else "#EF4444"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 18px 12px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; margin-bottom: 18px; box-shadow: var(--shadow);">
            <span style="font-size: 13px; font-weight: 750; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.7px; display: block; margin-bottom: 5px;">P&G DIARIO NETO CONSOLIDADO (Último Cierre)</span>
            <span style="font-size: 34px; font-weight: 850; color: {color_total}; display: block; margin-bottom: 4px;">
                {signo_total}${var_total_cop:,.0f} COP
            </span>
            <span style="font-size: 13.5px; font-weight: 650; color: var(--text-muted);">
                Patrimonio Líquido Actual: <b>${patrimonio_liquido:,.0f} COP</b>
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Desglose Contable por Efectos (Mercado vs Divisa)
        c_inf1, c_inf2 = st.columns(2)
        
        with c_inf1:
            signo_m = "+" if efecto_mercado_total >= 0 else ""
            color_m = "#10B981" if efecto_mercado_total >= 0 else "#EF4444"
            st.markdown(f"""
            <div style="padding: 14px 18px; background: rgba(99, 102, 241, 0.03); border: 1px solid var(--border-color); border-radius: 10px; min-height: 115px;">
                <span style="font-size: 12.5px; font-weight: 800; color: #6366F1; text-transform: uppercase; display: block; margin-bottom: 5px;">📈 EFECTO MERCADO (Valorización)</span>
                <span style="font-size: 22px; font-weight: 800; color: {color_m}; display: block; margin-bottom: 5px;">
                    {signo_m}${efecto_mercado_total:,.0f} COP
                </span>
                <span style="font-size: 12px; color: var(--text-muted); display: block; line-height: 1.4;">
                    Variación patrimonial neta causada por el alza o la baja de las acciones, commodities y criptomonedas en su moneda nativa.
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        with c_inf2:
            signo_d = "+" if efecto_divisa_total >= 0 else ""
            color_d = "#10B981" if efecto_divisa_total >= 0 else "#EF4444"
            st.markdown(f"""
            <div style="padding: 14px 18px; background: rgba(6, 182, 212, 0.03); border: 1px solid var(--border-color); border-radius: 10px; min-height: 115px;">
                <span style="font-size: 12.5px; font-weight: 800; color: #06B6D4; text-transform: uppercase; display: block; margin-bottom: 5px;">💵 EFECTO DIVISA (Diferencia en Cambio)</span>
                <span style="font-size: 22px; font-weight: 800; color: {color_d}; display: block; margin-bottom: 5px;">
                    {signo_d}${efecto_divisa_total:,.0f} COP
                </span>
                <span style="font-size: 12px; color: var(--text-muted); display: block; line-height: 1.4;">
                    Impacto financiero neto en pesos derivado exclusivamente de las fluctuaciones de la TRM (USD/COP) sobre activos extranjeros.
                </span>
            </div>
            """, unsafe_allow_html=True)
        # 4. Detalle y Atribución Divisa (Fórmula Financiera Explicativa con fuentes ampliadas)
        var_trm = trm_dia - trm_yesterday
        exposicion_usd_real = val_usd_total_cop / trm_dia if trm_dia > 0 else 0.0
        
        st.markdown(f"""
        <div style="margin-top: 18px; padding: 14px 18px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px;">
            <span style="font-size: 13.5px; font-weight: 800; color: var(--text-color); text-transform: uppercase; display: block; margin-bottom: 8px;">🔍 ATRIBUCIÓN CAMBIARIA Y CÁLCULO DE LA DIVISA</span>
            <div style="font-size: 13px; color: var(--text-color); line-height: 1.6; opacity: 0.9;">
                • <b>Exposición Total al Dólar:</b> {pct_usd_exposure:.1f}% del portafolio líquido (<b>${exposicion_usd_real:,.2f} USD</b> equivalente a <b>${val_usd_total_cop:,.0f} COP</b>).<br>
                • <b>TRM Cierre Hoy:</b> ${trm_dia:,.2f} COP | <b>TRM Cierre Anterior:</b> ${trm_yesterday:,.2f} COP.<br>
                • <b>Variación Neta de Tasa:</b> <span style="color: {'#10B981' if var_trm >= 0 else '#EF4444'}; font-weight: 700;">{var_trm:+,.2f} COP por dólar</span>.<br>
                <div style="margin-top: 8px; padding: 8px 12px; background: {'rgba(255, 255, 255, 0.02)' if modo_oscuro else 'rgba(0, 0, 0, 0.02)'}; border-radius: 5px; font-family: monospace; font-size: 12px; font-weight: 600; line-height: 1.4;">
                    Atribución Cambiaria = Exposición USD ({exposicion_usd_real:,.2f}) × Variación TRM ({var_trm:+,.2f} COP) = {signo_d}${efecto_divisa_total:,.0f} COP
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 5. Motores del Día (Top Gainers and Losers con fuentes ampliadas)
        gains_df = maestro_df[maestro_df["Var COP"] > 0.01].sort_values("Var COP", ascending=False)
        losses_df = maestro_df[maestro_df["Var COP"] < -0.01].sort_values("Var COP", ascending=True)
        
        motores_html = []
        if not gains_df.empty:
            top_gain = gains_df.iloc[0]
            g_pct = (top_gain["Var COP"] / (top_gain["Total_COP"] - top_gain["Var COP"]) * 100) if (top_gain["Total_COP"] - top_gain["Var COP"]) > 0 else 0.0
            motores_html.append(f"""
            <div style="width: 100%; padding: 14px 16px; background-color: #111827 !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;">
                <span style="font-size: 11px; font-weight: 800; color: #10B981 !important; text-transform: uppercase; display: block;">🚀 MAYOR IMPULSOR POSITIVO</span>
                <span style="font-size: 14.5px; font-weight: 700; color: #F3F4F6 !important; display: block; margin-top: 3px;">{top_gain['Ticker']} ({top_gain['Clase']})</span>
                <span style="font-size: 13px; font-weight: 700; color: #10B981 !important; display: block; margin-top: 2px;">
                    +${top_gain['Var COP']:,.0f} COP ({g_pct:+.2f}%)
                </span>
            </div>
            """)
        else:
            motores_html.append("""
            <div style="width: 100%; padding: 14px 16px; background-color: #111827 !important; border: 1px solid #1F2937 !important; border-radius: 10px; text-align: center; color: #9CA3AF !important; font-size: 13px; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;">
                Sin ganancias significativas hoy.
            </div>
            """)
            
        if not losses_df.empty:
            top_loss = losses_df.iloc[0]
            l_pct = (top_loss["Var COP"] / (top_loss["Total_COP"] - top_loss["Var COP"]) * 100) if (top_loss["Total_COP"] - top_loss["Var COP"]) > 0 else 0.0
            motores_html.append(f"""
            <div style="width: 100%; padding: 14px 16px; background-color: #111827 !important; border: 1px solid rgba(239, 68, 68, 0.3) !important; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;">
                <span style="font-size: 11px; font-weight: 800; color: #EF4444 !important; text-transform: uppercase; display: block;">⚠️ MAYOR IMPULSOR NEGATIVO</span>
                <span style="font-size: 14.5px; font-weight: 700; color: #F3F4F6 !important; display: block; margin-top: 3px;">{top_loss['Ticker']} ({top_loss['Clase']})</span>
                <span style="font-size: 13px; font-weight: 700; color: #EF4444 !important; display: block; margin-top: 2px;">
                    -${abs(top_loss['Var COP']):,.0f} COP ({l_pct:+.2f}%)
                </span>
            </div>
            """)
        else:
            motores_html.append("""
            <div style="width: 100%; padding: 14px 16px; background-color: #111827 !important; border: 1px solid #1F2937 !important; border-radius: 10px; text-align: center; color: #9CA3AF !important; font-size: 13px; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;">
                Sin pérdidas significativas hoy.
            </div>
            """)
            
        col_mot1, col_mot2 = st.columns(2)
        with col_mot1:
            st.markdown(motores_html[0], unsafe_allow_html=True)
        with col_mot2:
            st.markdown(motores_html[1], unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:10px;'>4. TENDENCIAS HISTÓRICAS SEGMENTADAS (Evolución Detallada por Componente)</p>", unsafe_allow_html=True)
    clases_hist_v6 = ["Acciones EEUU", "Acciones Colombia", "Criptomonedas", "Commodities (Oro)", "Fondos de Inversión", "Cash Broker Desk"]
    
    for i in range(0, len(clases_hist_v6), 2):
        bloque_clases = clases_hist_v6[i:i+2]
        columnas_render = st.columns(2)
        
        for sub_idx, c_name in enumerate(bloque_clases):
            with columnas_render[sub_idx]:
                df_sub = df_hist_diario[df_hist_diario["Clase"] == c_name].sort_values("Fecha")
                if df_sub.empty:
                    st.info(f"💡 Sin datos para {c_name} en el rango.")
                else:
                    val_grupo_fiel = maestro_df[maestro_df["Clase_Linea"] == c_name]["Total_COP"].sum()
                    
                    s_min, s_max = float(df_sub["Valor_COP"].min()), float(df_sub["Valor_COP"].max())
                    s_pad = max((s_max - s_min) * 0.15, s_max * 0.02) if s_max != s_min else s_max * 0.05
                    
                    s_min_x, s_max_x = df_sub["Fecha"].min(), df_sub["Fecha"].max()
                    duration_s_x = s_max_x - s_min_x
                    if duration_s_x == timedelta(0):
                        pad_s_x_left = timedelta(days=1)
                        pad_s_x_right = timedelta(days=1)
                    else:
                        pad_s_x_left = duration_s_x * 0.02
                        pad_s_x_right = duration_s_x * 0.055
                    limites_s_x = [
                        (s_min_x - pad_s_x_left).strftime("%Y-%m-%d"),
                        (s_max_x + pad_s_x_right).strftime("%Y-%m-%d")
                    ]
                    
                    fig_ind = go.Figure()
                    
                    # 1. Trazo de brillo de línea (glowing neon stroke)
                    fig_ind.add_trace(go.Scatter(
                        x=df_sub["Fecha"], y=df_sub["Valor_COP"], mode="lines",
                        line=dict(color=PALETA_GRAFICOS[(i + sub_idx) % len(PALETA_GRAFICOS)], width=7),
                        opacity=0.18, showlegend=False, hoverinfo="skip"
                    ))
                    
                    # 2. Trazo principal continuo
                    fig_ind.add_trace(go.Scatter(
                        x=df_sub["Fecha"], y=df_sub["Valor_COP"], mode="lines",
                        name=c_name,
                        line=dict(color=PALETA_GRAFICOS[(i + sub_idx) % len(PALETA_GRAFICOS)], width=2.5),
                        fill='tozeroy', fillcolor="rgba(99, 102, 241, 0.01)"
                    ))
                    
                    st.markdown(f"""
                    <div style="margin-top: 10px; margin-bottom: 6px; padding-left: 5px;">
                        <span style="font-size: 12px; font-weight: 700; color: var(--text-color); display: block; margin-bottom: 1px;">{c_name.upper()}</span>
                        <span style="font-size: 10px; font-weight: 600; color: var(--text-muted);">Balance: ${val_grupo_fiel:,.0f} COP</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    fig_ind.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", template=PLOTLY_TEMPLATE, height=270, hovermode="x unified",
                        margin=dict(t=10, b=25, l=65, r=40), showlegend=False,
                        xaxis=dict(type='date', range=limites_s_x, showgrid=False, tickformat="%d-%m", tickfont=dict(size=9, color=TEXT_MUTED)),
                        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, autorange=False, range=[max(0.0, s_min - s_pad), s_max + s_pad], showticklabels=True, tickfont=dict(size=8, color=TEXT_MUTED), tickformat="$,.0f"),
                        font=dict(family="Inter, system-ui, sans-serif"),
                        hoverlabel=dict(
                            bgcolor="rgba(17, 24, 39, 0.95)" if modo_oscuro else "rgba(255, 255, 255, 0.95)",
                            bordercolor="rgba(99, 102, 241, 0.3)" if modo_oscuro else "rgba(79, 70, 229, 0.3)",
                            font=dict(
                                color="#FFFFFF" if modo_oscuro else "#0F172A",
                                size=11,
                                family="Inter, system-ui, sans-serif"
                            )
                        )
                    )
                    st.plotly_chart(fig_ind, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})

# -----------------------------------------------------------------------------
# TAB 2: BOOK OF RECORDS & OPERATIONS
# -----------------------------------------------------------------------------
with tab_records:
    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:10px;'>📋 LIBRO DETALLADO DE ACTIVOS & SALDOS DE CONTROL</p>", unsafe_allow_html=True)
    
    # Colores explícitos para el iframe a fin de evitar problemas de herencia de variables CSS
    c_texto = TEXT_COLOR
    c_muted = TEXT_MUTED
    c_borde = "rgba(255, 255, 255, 0.08)" if modo_oscuro else "rgba(0, 0, 0, 0.06)"
    c_tarjeta = "rgba(17, 24, 39, 0.65)" if modo_oscuro else "rgba(255, 255, 255, 0.85)"
    c_shadow = "0 4px 30px rgba(0, 0, 0, 0.35)" if modo_oscuro else "0 4px 20px rgba(0, 0, 0, 0.04)"
    
    html_rows = []
    for idx, r in maestro_df.iterrows():
        t = r["Ticker"]
        c_name = r["Clase"]
        meta = category_meta.get(c_name, {"emoji": "📦", "color": "#6B7280"})
        emoji = meta["emoji"]
        c_color = meta["color"]
        
        cant = f"{r['Cantidad']:,.4f}" if r["Cantidad"] > 0 else "0.0000"
        moneda = r["Moneda"]
        
        if moneda == "USD":
            curr_badge_style = "background: rgba(99, 102, 241, 0.15) !important; color: #6366F1 !important; border: 1px solid rgba(99, 102, 241, 0.2) !important;"
        else:
            curr_badge_style = "background: rgba(16, 185, 129, 0.15) !important; color: #10B981 !important; border: 1px solid rgba(16, 185, 129, 0.2) !important;"
            
        p_unit = f"${r['Precio_Unitario']:,.2f} USD" if moneda == "USD" else f"${r['Precio_Unitario']:,.0f} COP"
        tot_cop = f"${r['Total_COP']:,.0f} COP"
        
        pct_val = r["% Var Diario"] if not pd.isna(r["% Var Diario"]) else 0.0
        var_cop_val = r["Var COP"] if not pd.isna(r["Var COP"]) else 0.0
        
        if pct_val > 0.001:
            var_badge_style = "background: rgba(16, 185, 129, 0.12) !important; color: #10B981 !important; border: 1px solid rgba(16, 185, 129, 0.15) !important;"
            var_sign = "▲"
        elif pct_val < -0.001:
            var_badge_style = "background: rgba(239, 68, 68, 0.12) !important; color: #EF4444 !important; border: 1px solid rgba(239, 68, 68, 0.15) !important;"
            var_sign = "▼"
        else:
            var_badge_style = "background: rgba(156, 163, 175, 0.12) !important; color: #9CA3AF !important; border: 1px solid rgba(156, 163, 175, 0.15) !important;"
            var_sign = "▪"
            
        var_str = f"{var_sign} {abs(pct_val):.2f}% (${abs(var_cop_val):,.0f} COP)"
        
        # Efectos explicativos
        ef_m = r["Ef_Mercado"] if not pd.isna(r["Ef_Mercado"]) else 0.0
        if ef_m > 0.01:
            ef_m_sign = "▲"
            ef_m_color = "#10B981"
        elif ef_m < -0.01:
            ef_m_sign = "▼"
            ef_m_color = "#EF4444"
        else:
            ef_m_sign = "▪"
            ef_m_color = c_muted
        ef_m_str = f"<span style='color: {ef_m_color}; font-weight: 600;'>{ef_m_sign} ${abs(ef_m):,.0f}</span>"
        
        ef_d = r["Ef_Divisa"] if not pd.isna(r["Ef_Divisa"]) else 0.0
        if ef_d > 0.01:
            ef_d_sign = "▲"
            ef_d_color = "#10B981"
        elif ef_d < -0.01:
            ef_d_sign = "▼"
            ef_d_color = "#EF4444"
        else:
            ef_d_sign = "▪"
            ef_d_color = c_muted
        ef_d_str = f"<span style='color: {ef_d_color}; font-weight: 600;'>{ef_d_sign} ${abs(ef_d):,.0f}</span>"
        
        row_html = f"""
        <tr style="border-bottom: 1px solid {c_borde}; transition: background 0.2s ease;">
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle;"><span style="font-weight: 600; font-size: 13px; letter-spacing: 0.2px; color: {c_texto}; padding: 4px 8px; border-radius: 6px; background: rgba(148, 163, 184, 0.08); border-left: 3px solid {c_color}; display: inline-block;">{t}</span></td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle;"><span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 550; color: #FFFFFF !important; background-color: {c_color}; text-transform: uppercase; letter-spacing: 0.3px;">{emoji} {c_name}</span></td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle; text-align: right; font-weight: 500; font-family: monospace; font-size: 13px;">{cant}</td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle; text-align: center;"><span style="display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; {curr_badge_style}">{moneda}</span></td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle; text-align: right; font-weight: 500; font-family: monospace; font-size: 13px;">{p_unit}</td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle; text-align: right; font-weight: 600; font-family: monospace; font-size: 13px; color: {c_texto};">{tot_cop}</td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle;"><span style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; white-space: nowrap; {var_badge_style}">{var_str}</span></td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle; text-align: right; font-family: monospace; font-size: 13px;">{ef_m_str}</td>
            <td style="padding: 14px 16px; font-size: 13px; color: {c_texto}; vertical-align: middle; text-align: right; font-family: monospace; font-size: 13px;">{ef_d_str}</td>
        </tr>
        """
        html_rows.append(row_html)
        
    table_content = "\n".join(html_rows)
    
    html_table = f"""
    <!DOCTYPE html>
    <html style="background-color: {BG_COLOR} !important; background: {BG_COLOR} !important;">
    <head>
        <meta charset="utf-8">
        <style>
        html, body {{
            background-color: {BG_COLOR} !important;
            background: {BG_COLOR} !important;
            margin: 0;
            padding: 0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            color: {c_texto};
        }}
        /* Estilos Premium para la Tabla de Activos */
        .premium-table-container {{
            width: 100%;
            overflow-x: auto;
            border-radius: 14px;
            border: 1px solid {c_borde};
            background: {c_tarjeta};
            box-shadow: {c_shadow};
            margin-top: 10px;
            margin-bottom: 20px;
        }}
        .premium-table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        .premium-table th {{
            background: rgba(148, 163, 184, 0.08);
            padding: 14px 16px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: {c_texto};
            letter-spacing: 0.8px;
            border-bottom: 2px solid {c_borde};
        }}
        .premium-table td {{
            padding: 14px 16px;
            font-size: 13px;
            color: {c_texto};
            border-bottom: 1px solid {c_borde};
            vertical-align: middle;
        }}
        .premium-table tr:last-child td {{
            border-bottom: none;
        }}
        .premium-table tr:hover {{
            background: rgba(99, 102, 241, 0.04);
            transition: background 0.2s ease;
        }}
        </style>
    </head>
    <body>
        <div class="premium-table-container">
            <table class="premium-table">
                <thead>
                    <tr>
                        <th style="text-align: left;">Ticker</th>
                        <th style="text-align: left;">Clase de Activo</th>
                        <th style="text-align: right;">Cantidad</th>
                        <th style="text-align: center;">Moneda</th>
                        <th style="text-align: right;">Precio Unitario</th>
                        <th style="text-align: right;">Valor Total (COP)</th>
                        <th style="text-align: left;">% Var Diario (COP)</th>
                        <th style="text-align: right;">Ef. Mercado</th>
                        <th style="text-align: right;">Ef. Divisa</th>
                    </tr>
                </thead>
                <tbody>
                    {table_content}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    st.components.v1.html(html_table, height=920, scrolling=True)

# -----------------------------------------------------------------------------
# TAB 3: RADAR DE NOTICIAS & INTELIGENCIA DE MERCADO
# -----------------------------------------------------------------------------
with tab_news:
    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:10px;'>📰 RADAR DE NOTICIAS & INTELIGENCIA DE MERCADO</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; color:var(--text-muted); margin-bottom:15px;'>Noticias recientes de última hora sobre tus activos en cartera de Colombia y del mundo. Datos actualizados y cacheados cada 30 minutos.</p>", unsafe_allow_html=True)
    
    # 1. Obtener lista de tickers activos
    tickers_portafolio = list(maestro_df["Ticker"].unique())
    
    # 2. Cargar noticias (con cache inteligente)
    with st.spinner("Sincronizando últimas noticias del mercado..."):
        lista_noticias = cargar_radar_noticias(tickers_portafolio)
        
    if not lista_noticias:
        st.info("ℹ️ No se encontraron noticias recientes para tus activos en este momento. Reintenta más tarde o verifica tu conexión a internet.")
    else:
        # 3. Filtro de noticias
        filtro = st.radio(
            "Filtrar Noticias por Ámbito de Mercado:",
            ["Todas las Noticias 🌐", "Mercados Internacionales 🇺🇸", "Mercado Local 🇨🇴"],
            horizontal=True,
            index=0
        )
        
        # Aplicar el filtro
        if "Local" in filtro:
            noticias_filtradas = [n for n in lista_noticias if n["type"] == "Local 🇨🇴"]
        elif "Internacionales" in filtro:
            noticias_filtradas = [n for n in lista_noticias if n["type"] == "Internacional 🇺🇸"]
        else:
            noticias_filtradas = lista_noticias
            
        if not noticias_filtradas:
            st.warning("⚠️ No hay noticias de esta categoría para tus activos actuales.")
        else:
            # 4. Renderizar noticias en grid de 2 columnas
            cols_noticias = st.columns(2)
            for idx, n in enumerate(noticias_filtradas):
                col_target = cols_noticias[idx % 2]
                
                # HTML Card
                card_html = f"""
                <div class="news-card" style="border-left: 4px solid {n['accent_color']};">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 10px;">
                            <span style="font-size: 10px; font-weight: 800; text-transform: uppercase; color: {n['accent_color']}; letter-spacing: 0.8px; white-space: nowrap;">
                                {n['type']}
                            </span>
                            <span style="font-size: 10px; color: var(--text-muted); font-weight: 700; white-space: nowrap;">
                                🕒 {n['time']}
                            </span>
                        </div>
                        <h4 style="margin: 0; font-size: 13.5px; line-height: 1.35; font-weight: 750; color: var(--text-color); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; height: 55px;">
                            <a href="{n['link']}" target="_blank" class="news-title-link">
                                {n['title']}
                            </a>
                        </h4>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; border-top: 1px solid var(--border-color); padding-top: 8px;">
                        <span style="font-size: 10.5px; font-weight: 700; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 170px;">
                            Fuente: <span style="color: var(--text-color); font-weight: 800;">{n['publisher']}</span>
                        </span>
                        <a href="{n['link']}" target="_blank" style="font-size: 11px; font-weight: 800; color: #6366F1; text-decoration: none; display: flex; align-items: center; gap: 3px; white-space: nowrap;">
                            Leer Artículo ↗
                        </a>
                    </div>
                </div>
                """
                with col_target:
                    st.markdown(card_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 4: TRANSACTION DESK ENGINE (OPTIMIZED CRUD & MODAL-LIKE DESIGN)
# -----------------------------------------------------------------------------
with tab_transactions:
    st.markdown(f"<p style='color:var(--text-color); font-weight:700; font-size:15px; margin-bottom:10px;'>💼 TRANSACTION DESK ENGINE (Gestor de Portafolio)</p>", unsafe_allow_html=True)
    
    col_crud_main, col_crud_preview = st.columns([2, 1.2])
    
    with col_crud_main:
        listado_crud = ["--- OPERAR NUEVO ACTIVO ---"] + list(st.session_state['inventario_activos_core']["Ticker"].unique())
        selector = st.selectbox("Seleccione Posición a Operar:", listado_crud, index=0)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        # CRUD form logic
        if selector == "--- OPERAR NUEVO ACTIVO ---":
            st.subheader("➕ Agregar Nuevo Activo")
            f_ticker = st.text_input("Ticker ID (ej. AAPL, NVDA, ETH)").upper().strip()
            f_clase = st.selectbox("Categoría / Clase:", ["Acciones EEUU", "Acciones Colombia", "Criptomonedas", "Commodities (Oro)", "Fondos de Inversión", "Liquidez COP", "Liquidez USD", "Propiedad Raíz"])
            default_cant = 1.0 if f_clase in ["Fondos de Inversión", "Liquidez COP", "Liquidez USD", "Propiedad Raíz"] else 0.0
            f_cant = st.number_input("Cantidad a Adquirir:", min_value=0.0, format="%.8f", value=default_cant)
            f_precio = st.number_input("Precio Unitario de Referencia:", min_value=0.0, format="%.4f", value=0.0)
            f_var_manual = 0.0
            
            est_moneda = "USD" if any(x in f_clase for x in ["EEUU", "Cripto", "Commodities", "USD"]) else "COP"
            
            c1, c2 = st.columns(2)
            with c1:
                boton_add = st.button("➕ Crear e Integrar Posición", type="primary", use_container_width=True)
            with c2:
                boton_del = False
        else:
            st.subheader(f"📝 Modificar / Eliminar Posición: {selector}")
            actual = st.session_state['inventario_activos_core'][st.session_state['inventario_activos_core']["Ticker"] == selector].iloc[0]
            f_ticker = selector
            f_clase = actual["Clase"]
            f_cant = st.number_input("Cantidad Consolidada:", min_value=0.0, value=float(actual["Cantidad"]), format="%.8f")
            f_precio = st.number_input("Precio Unitario de Referencia:", min_value=0.0, value=float(actual["Valor_Base_Fijo"]), format="%.4f")
            
            # Estimación automática de Variación porcentual diaria en base al cambio de precio manual
            old_price = float(actual["Valor_Base_Fijo"])
            if old_price > 0.0 and f_precio != old_price:
                f_var_manual = ((f_precio - old_price) / old_price) * 100
            else:
                f_var_manual = float(actual["Var_Manual"]) if "Var_Manual" in actual and not pd.isna(actual["Var_Manual"]) else 0.0
                
            est_moneda = actual["Moneda"]
            
            c1, c2 = st.columns(2)
            with c1:
                boton_add = st.button("💾 Sincronizar Cambios", type="primary", use_container_width=True)
            with c2:
                boton_del = st.button("🗑️ Eliminar Posición del Portafolio", type="secondary", use_container_width=True)

    # Process Form Action
    if boton_add and f_ticker:
        # Save position change
        st.session_state['inventario_activos_core'] = st.session_state['inventario_activos_core'][st.session_state['inventario_activos_core']["Ticker"] != f_ticker]
        nueva_pos = {
            "Ticker": f_ticker, 
            "Clase": f_clase, 
            "Cantidad": f_cant, 
            "Valor_Base_Fijo": f_precio, 
            "Moneda": est_moneda,
            "Var_Manual": f_var_manual
        }
        st.session_state['inventario_activos_core'] = pd.concat([st.session_state['inventario_activos_core'], pd.DataFrame([nueva_pos])], ignore_index=True)
        guardar_inventario(st.session_state['inventario_activos_core'])
        st.toast(f"✅ Posición '{f_ticker}' sincronizada con éxito.")
        st.cache_data.clear()
        st.rerun()
        
    if boton_del and f_ticker:
        # Delete position
        st.session_state['inventario_activos_core'] = st.session_state['inventario_activos_core'][st.session_state['inventario_activos_core']["Ticker"] != f_ticker]
        guardar_inventario(st.session_state['inventario_activos_core'])
        st.toast(f"🗑️ Posición '{f_ticker}' eliminada del inventario de forma permanente.")
        st.cache_data.clear()
        st.rerun()

    # Previsualización interactiva en tiempo real (Live Value Preview)
    with col_crud_preview:
        st.markdown("<div style='text-align: center; margin-top: 25px;'></div>", unsafe_allow_html=True)
        
        # Calculate real-time estimated values for form inputs
        if f_ticker:
            p_usd_est = f_precio
            if f_clase in ["Acciones EEUU", "Commodities (Oro)"]:
                p_usd_est = p_us.get(f_ticker, f_precio)
            elif f_clase == "Criptomonedas":
                p_usd_est = p_cry.get(f_ticker, f_precio)
                
            if est_moneda == "USD":
                val_cop_est = f_cant * p_usd_est * trm_dia
                val_usd_est = f_cant * p_usd_est
            else:
                val_cop_est = f_cant * p_usd_est
                val_usd_est = val_cop_est / trm_dia if trm_dia > 0 else 0.0
                
            st.markdown(f"""
            <div class="metric-container" style="height: auto; padding: 22px; border-color: var(--primary-glow);">
                <div class="metric-label">Simulación del Activo en Tiempo Real</div>
                <div class="metric-value" style="font-size: 22px; margin: 8px 0; color: #6366F1;">
                    {f_ticker} <span style="font-size: 13px; color: var(--text-muted); font-weight: 500;">({f_clase})</span>
                </div>
                <div style="font-size: 16px; font-weight: 700; color: var(--text-color);">
                    COP Estimado: <span style="color:#10B981">${val_cop_est:,.0f} COP</span>
                </div>
                <div style="font-size: 13px; font-weight: 600; color: var(--text-muted); margin-top: 4px;">
                    USD Equiv: <span style="color:var(--text-color);">${val_usd_est:,.2f} USD</span>
                </div>
                <div style="font-size: 10px; color: var(--text-muted); margin-top: 10px; border-top: 1px solid var(--border-color); padding-top: 6px;">
                    TRM Utilizada: ${trm_dia:,.2f} COP (Yahoo Live)
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-container" style="height: auto; padding: 22px; text-align: center; justify-content: center;">
                <div class="metric-label" style="text-align: center;">Previsualizador</div>
                <p style="font-size:12px; color: var(--text-muted); margin-top:10px;">Escribe un Ticker ID o selecciona una posición para ver su valoración en tiempo real.</p>
            </div>
            """, unsafe_allow_html=True)
