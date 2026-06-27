import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time

# Configuração da Página
st.set_page_config(page_title="CYBER RIG // TELEMETRY", layout="wide", page_icon="⚡")

# --- INJEÇÃO DE CSS CYBERPUNK ---
st.markdown("""
<style>
    /* Fundo principal escurão e fonte futurista */
    .stApp {
        background-color: #08080C;
        color: #00F0FF;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Títulos com brilho Neon */
    h1, h2, h3 {
        color: #00FF66 !important;
        text-shadow: 0 0 10px rgba(0, 255, 102, 0.5);
        font-weight: 800 !important;
        letter-spacing: 2px;
    }
    
    /* Cards de Métricas Customizados */
    div[data-testid="metric-container"] {
        background: #12121C;
        border: 1px solid #00F0FF;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
        padding: 15px;
        border-radius: 4px;
        border-left: 5px solid #00FF66;
    }
    
    /* Cor dos rótulos das métricas */
    div[data-testid="stMetricLabel"] > label {
        color: #A0A0B0 !important;
        font-size: 0.9rem !important;
    }
    
    /* Cor dos valores grandes das métricas */
    div[data-testid="stMetricValue"] > div {
        color: #00FF66 !important;
        text-shadow: 0 0 8px rgba(0, 255, 102, 0.6);
    }
    
    /* Botão Desligar (Estilo Alerta Vermelho) */
    div.stButton > button:first-child {
        background-color: #1A0008;
        color: #FF0055;
        border: 2px solid #FF0055;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.4);
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #FF0055;
        color: #000000;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.8);
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM BANCO ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- FORÇA O STREAMLIT A LER DADOS NOVO A CADA 5 SEGUNDOS ---
@st.cache_data(ttl=5)
def buscar_dados():
    resposta = supabase.table("status_rig").select("*").order("id", desc=True).limit(40).execute()
    return resposta.data

def enviar_comando(comando):
    supabase.table("status_rig").insert({
        "hashrate": "0 H/s",
        "temperatura": "0 °C",
        "comando_status": comando
    }).execute()

# --- CABEÇALHO ---
st.title("⚡ CYBER_RIG // TELEMETRY_OS v1.0")
st.markdown("`SYSTEM STATUS: SECURE CONNECTION ESTABLISHED`")
st.divider()

col_top1, col_top2 = st.columns([1, 6])
with col_top1:
    if st.button("🔄 REBOOT SYNC"):
        st.rerun()

dados = buscar_dados()

if dados:
    dado_atual = dados[0]
    
    # Grid de Métricas Principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="HASHRATE ATIVO", value=dado_atual.get("hashrate", "0 H/s"))
    with col2:
        st.metric(label="TEMP NÚCLEO", value=dado_atual.get("temperatura", "0 °C"))
    with col3:
        status_code = dado_atual.get("comando_status", "rodar")
        status_display = "ONLINE // MINING" if status_code == "rodar" else "HALTED // STOPPED"
        st.metric(label="STATUS OPERACIONAL", value=status_display)

    st.markdown("### 📊 FLUXO DE HASHING EM TEMPO REAL")
    
    # Tratamento de dados para Gráfico Moderno
    df = pd.DataFrame(dados)
    df['Hashrate (H/s)'] = df['hashrate'].str.extract(r'([0-9.]+)').astype(float)
    df['Temp (°C)'] = df['temperatura'].str.extract(r'([0-9.]+)').astype(float)
    df = df.iloc[::-1].reset_index(drop=True)
    
    # Gráfico com cores nativas adaptadas ao tema escuro
    st.area_chart(df[['Hashrate (H/s)']], color="#00FF66")
    
    with st.expander("👁️ VER LOGS BRUTOS DO SISTEMA"):
        st.dataframe(df[['created_at', 'hashrate', 'temperatura', 'comando_status']], use_container_width=True)

else:
    st.info("Aguardando pulso de dados da máquina local... Inicie o script no terminal.")

st.divider()

# Painel de Controle Crítico
st.markdown("### 🎛️ CONTROLE DE ENERGIA")
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🚨 ABORTAR OPERAÇÃO (KILL SWITCH)", use_container_width=True):
        enviar_comando("parar")
        st.toast("Sinal de parada emergencial enviado!")

with col_btn2:
    if st.button("⚡ RESTAURAR ENERGIA (START)", use_container_width=True):
        enviar_comando("rodar")
        st.toast("Sistema liberado para mineração.")
