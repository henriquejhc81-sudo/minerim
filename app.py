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
st.markdown("---")
st.markdown("### 🏛️ RELATÓRIO FORENSE INSTITUCIONAL")

# Coletando a data e hora atual do sistema
import pandas as pd
data_hora_atual = pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')

# Separando quem está seguro e quem está em perigo
ativos_quarentena = df[df['Veredicto'].str.contains('QUARENTENA', na=False)]
ativos_liberados = df[df['Veredicto'].str.contains('LIBERADO', na=False)]

# Definindo o Status do Mercado
if len(ativos_quarentena) > len(ativos_liberados):
    status_mercado = "🔴 ALERTA VERMELHO (Risco Sistêmico Alto)"
elif len(ativos_quarentena) > 0:
    status_mercado = "🟡 ATENÇÃO (Risco Moderado)"
else:
    status_mercado = "🟢 ESTÁVEL (Risco Controlado)"

# Escrevendo o relatório no estilo institucional
relatorio = f"""
> **DATA DA ANÁLISE:** {data_hora_atual}  
> **DIRETRIZ DE OPERAÇÃO:** {status_mercado}  

**RESUMO EXECUTIVO:**  
No presente momento, a varredura algorítmica de telemetria analisou a cesta de ativos designada. Constata-se que **{len(ativos_quarentena)}** ativos encontram-se em estado de exceção (Quarentena), devido a anomalias no RSI ou distanciamento da EMA 20, enquanto **{len(ativos_liberados)}** operam dentro dos parâmetros de normalidade e segurança.

**LAUDO DE EXAUSTÃO:**
"""
st.markdown(relatorio)

# Mostra o motivo exato de cada moeda que está em perigo
if not ativos_quarentena.empty:
    for index, row in ativos_quarentena.iterrows():
        st.warning(f"⚠️ **Ativo {row['Ativo']} bloqueado.** Motivo detectado: {row['Motivo']}")
else:
    st.success("✅ **Nenhuma anomalia detectada.** Todos os ativos monitorados estão em zona segura para operação.")
