import streamlit as st
import pandas as pd
import motor_mestre 

st.set_page_config(
    page_title="MESTRE BLOOMBERG // TELEMETRY_OS",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .titulo-neon {
        color: #00FF41;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        text-shadow: 0 0 5px #00FF41;
    }
    .status-box {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #00FF41;
        font-family: 'Courier New', Courier, monospace;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-neon">⚡ MESTRE BLOOMBERG // TELEMETRY_OS v2.0</h1>', unsafe_allow_html=True)
st.markdown('<div class="status-box">SYSTEM STATUS: OPERACIONAL // RISCO CONTROLADO</div>', unsafe_allow_html=True)
st.write("---")

if st.button("🔄 REBOOT SYNC // ATUALIZAR DADOS"):
    st.cache_data.clear() 

with st.spinner("Conectando aos satélites da Binance e calculando scores..."):
    dados_mercado = motor_mestre.varredura_global()
    df = pd.DataFrame(dados_mercado)

def colorir_veredicto(val):
    if "LIBERADO" in str(val):
        return 'color: #00FF41; font-weight: bold;'
    elif "QUARENTENA" in str(val):
        return 'color: #FF0000; font-weight: bold;'
    elif "FALHA" in str(val):
        return 'color: #FF9900; font-weight: bold;'
    return 'color: white;'

df_estilizado = df.style.map(colorir_veredicto, subset=['Veredicto'])

col1, col2, col3 = st.columns(3)

# CORREÇÃO CRÍTICA AQUI: Pega o preço com segurança e trata erros da Binance
if not df.empty and 'Preço' in df.columns:
    preco_btc = df.iloc[0]['Preço']
else:
    preco_btc = "N/A"

total_quarentena = len(df[df['Veredicto'].str.contains('QUARENTENA')]) if not df.empty else 0

with col1:
    st.metric(label="Rei do Mercado (BTC)", value=preco_btc)
with col2:
    st.metric(label="Ativos em Quarentena", value=f"{total_quarentena} / 10")
with col3:
    st.metric(label="Circuit Breaker Macro", value="ARMADO", delta="Defesa Ativa")

st.write("---")
st.markdown('<h3 class="titulo-neon">📊 RADAR TÁTICO DE EXAUSTÃO (15m)</h3>', unsafe_allow_html=True)

st.dataframe(
    df_estilizado,
    use_container_width=True,
    hide_index=True,
    height=400
)
