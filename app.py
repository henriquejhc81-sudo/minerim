import streamlit as st
import pandas as pd
import motor_mestre # Importa o nosso motor matemático

# 1. Configuração da Página (Design e Título)
st.set_page_config(
    page_title="MESTRE BLOOMBERG // TELEMETRY_OS",
    page_icon="⚡",
    layout="wide"
)

# 2. CSS Personalizado (Estética Cyber_Rig / Neon)
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
    }
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

# 3. Cabeçalho do Painel
st.markdown('<h1 class="titulo-neon">⚡ MESTRE BLOOMBERG // TELEMETRY_OS v2.0</h1>', unsafe_allow_html=True)
st.markdown('<div class="status-box">SYSTEM STATUS: OPERACIONAL // RISCO CONTROLADO</div>', unsafe_allow_html=True)
st.write("---")

# Botão de atualização manual (Como o seu antigo "Reboot Sync")
if st.button("🔄 REBOOT SYNC // ATUALIZAR DADOS"):
    st.cache_data.clear() # Limpa o cache para forçar a busca de novos dados

# 4. Buscando os dados do Motor Mestre
with st.spinner("Conectando aos satélites da Binance e calculando scores..."):
    # Chama a função que varre as 10 moedas
    dados_mercado = motor_mestre.varredura_global()
    df = pd.DataFrame(dados_mercado)

# 5. Lógica de Cores para a Tabela (Verde = Liberado, Vermelho = Quarentena)
def colorir_veredicto(val):
    if "LIBERADO" in str(val):
        return 'color: #00FF41; font-weight: bold;'
    elif "QUARENTENA" in str(val):
        return 'color: #FF0000; font-weight: bold;'
    return 'color: white;'

# Aplica a cor apenas na coluna "Veredicto"
df_estilizado = df.style.map(colorir_veredicto, subset=['Veredicto'])

# 6. Exibindo as Métricas Globais Rápidas
col1, col2, col3 = st.columns(3)

# Pegando o preço do BTC para exibir no topo (ele é o primeiro da lista G1)
preco_btc = df.iloc[0]['Preço'] if not df.empty else "N/A"
total_quarentena = len(df[df['Veredicto'].str.contains('QUARENTENA')]) if not df.empty else 0

with col1:
    st.metric(label="Rei do Mercado (BTC)", value=preco_btc)
with col2:
    st.metric(label="Ativos em Quarentena", value=f"{total_quarentena} / 10")
with col3:
    st.metric(label="Circuit Breaker Macro", value="ARMADO", delta="Defesa Ativa")

st.write("---")
st.markdown('<h3 class="titulo-neon">📊 RADAR TÁTICO DE EXAUSTÃO (15m)</h3>', unsafe_allow_html=True)

# 7. Desenhando a Tabela na Tela
st.dataframe(
    df_estilizado,
    use_container_width=True,
    hide_index=True,
    height=400
)
