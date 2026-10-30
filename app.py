import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

# Configurazione della pagina
st.set_page_config(
    page_title="Modine HTS - Metal Price & Cost Intelligence",
    page_icon="📈",
    layout="wide",
)

st.title("🎛️ Modine HTS - Copper & Aluminum Intelligence Dashboard")
st.markdown(
    "Monitoraggio in tempo reale, trend storici e analisi dei **Conversion Premiums** e dei costi di sbarco (*Landed Cost*) per la divisione HTS."
)

# Sidebar per i filtri
st.sidebar.header("⚙️ Parametri di Controllo")
metal_choice = st.sidebar.selectbox(
    "Seleziona Metallo",
    ["Rame (Copper - Tubi/LWC)", "Alluminio (Aluminum - Alette/Coils)"],
)
region_choice = st.sidebar.selectbox(
    "Cluster Geografico", ["Global Master", "EMEA", "Americas", "APAC"]
)
time_frame = st.sidebar.selectbox(
    "Orizzonte Storico", ["1M", "6M", "1Y", "5Y", "Max"]
)

# Mappatura dei ticker finanziari
ticker_symbol = "HG=F" if "Rame" in metal_choice else "ALI=F"


@st.cache_data
def load_market_data(ticker, period):
  df = yf.download(ticker, period=period, interval="1d")
  return df


df_market = load_market_data(ticker_symbol, time_frame.lower().replace("max", "max"))

# Layout a schede
tab1, tab2, tab3 = st.tabs(
    [
        "📊 Mercato Real-Time & Storico",
        "💰 Cost Stack & Conversion Premiums",
        "🌍 Landed Cost & TCO Simulator",
    ]
)

# --- TAB 1: MERCATO ---
with tab1:
  st.subheader(f"Andamento Prezzo Spot ({metal_choice})")

  if not df_market.empty:
    current_price = df_market["Close"].iloc[-1]
    prev_price = df_market["Close"].iloc[-2]
    delta_price = float(current_price - prev_price)

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Prezzo Odierno", f"${current_price:.2f} / MT", f"{delta_price:.2f}"
    )
    col2.metric("Ticker Monitorato", ticker_symbol)
    col3.metric("Fonte Dati", "Yahoo Finance (Futures)")

    fig = px.line(
        df_market,
        x=df_market.index,
        y="Close",
        title=f"Trend Storico - {metal_choice}",
        labels={"Close": "Prezzo ($)", "Index": "Data"},
    )
    st.plotly_chart(fig, use_container_width=True)
  else:
    st.warning("Dati di mercato temporaneamente non disponibili.")

# --- TAB 2: COST STACK & PREMIUMS ---
with tab2:
  st.subheader("Analisi della Formula di Prezzo (Price Structure)")
  st.latex(
      r"\text{Total Landed Cost} = \text{Base Metallo (LME/COMEX)} + \text{Mill Fabrication Fee} + \text{Freight} + \text{Duty}"
  )

  cost_breakdown = {
      "Componente di Spesa": [
          "Base Metallo Spot",
          "Premio di Trasformazione (Tubi Rame / Alette)",
          "Transformation Costs (EMEA vs Asia)",
          "Packaging & Certificazioni",
      ],
      "Stima Valore ($/MT)": [
          "Indicizzato (LME/COMEX)",
          "$800 - $1.400 / MT",
          "Variabile per regione",
          "Standard industriale",
      ],
      "Impatto sul TCO HTS": [
          "Coperto da clausole Pass-Through",
          "Alti volumi in Europa e Americhe",
          "Leva di negoziazione globale",
          "Minimo impatto percentuale",
      ],
  }
  st.dataframe(pd.DataFrame(cost_breakdown), use_container_width=True)

# --- TAB 3: LANDED COST & TCO SIMULATOR ---
with tab3:
  st.subheader(
      f"Simulatore Landed Cost per il cluster: **{region_choice}**"
  )
  st.info(
      "Usa i cursori per simulare l'impatto di dazi, noli e premi di conversione sul costo finale di approvvigionamento."
  )

  col_a, col_b = st.columns(2)
  with col_a:
    sim_base = st.number_input(
        "Base Metallo ($/MT)", value=9000.0, step=100.0
    )
    sim_conv = st.number_input(
        "Conversion Premium / Fab Fee ($/MT)", value=1200.0, step=50.0
    )
  with col_b:
    sim_freight = st.number_input(
        "Costo Nolo / Logistica ($/MT)", value=250.0, step=25.0
    )
    sim_duty = st.number_input(
        "Dazi Doganali / Tariffe (%)", value=4.8, step=0.1
    )

  duty_value = (sim_base + sim_conv) * (sim_duty / 100.0)
  total_landed = sim_base + sim_conv + sim_freight + duty_value

  st.metric(
      label="Costo di Sbarco Totale Stimato (Landed Cost)",
      value=f"${total_landed:.2f} / MT",
      delta=f"Dazi inclusi: ${duty_value:.2f}",
  )
