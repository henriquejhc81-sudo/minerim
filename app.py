import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time

st.set_page_config(page_title="Rig Management System", layout="wide")

# --- CONEXÃO COM BANCO ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

def buscar_dados():
    # Busca os últimos 50 registros para montar o gráfico
    resposta = supabase.table("status_rig").select("*").order("id", desc=True).limit(50).execute()
    return resposta.data

def enviar_comando(comando):
    supabase.table("status_rig").insert({
        "hashrate": "0 H/s",
        "temperatura": "0 °C",
        "comando_status": comando
    }).execute()

st.title("⛏️ Central de Mineração Privada")

# Botão de refresh manual
if st.button("🔄 Atualizar Dados"):
    st.rerun()

dados = buscar_dados()

if dados:
    dado_atual = dados[0] # O dado mais recente
    
    # Layout Superior
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Hashrate Atual", value=dado_atual.get("hashrate", "0 H/s"))
    with col2:
        st.metric(label="Temperatura da CPU/GPU", value=dado_atual.get("temperatura", "0 °C"))
    with col3:
        status = "🟢 Online" if dado_atual.get("comando_status") == "rodar" else "🔴 Parado"
        st.metric(label="Status da Rig", value=status)

    st.subheader("📈 Histórico de Desempenho (Últimas Leituras)")
    
    # Tratamento de dados para o gráfico
    df = pd.DataFrame(dados)
    
    # Limpa os dados de string para float (ex: "1450 H/s" -> 1450.0)
    df['hashrate_num'] = df['hashrate'].str.extract(r'([0-9.]+)').astype(float)
    df['temp_num'] = df['temperatura'].str.extract(r'([0-9.]+)').astype(float)
    
    # Inverte o dataframe para o gráfico fluir da esquerda (antigo) para a direita (novo)
    df = df.iloc[::-1].reset_index(drop=True)
    
    st.line_chart(df[['hashrate_num', 'temp_num']])

else:
    st.warning("Aguardando dados da máquina local...")

st.divider()

st.subheader("⚙️ Comandos Remotos")
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🔴 Desligar Minerador Remotamente", use_container_width=True):
        enviar_comando("parar")
        st.error("Comando de PARADA enviado para a Rig! Ela deve desligar no próximo ciclo de leitura (10s).")

with col_btn2:
    if st.button("🟢 Resetar Comando para Rodar", use_container_width=True):
        enviar_comando("rodar")
        st.success("Comando resetado. A máquina não irá iniciar sozinha, mas o bloqueio de parada foi removido do banco.")
