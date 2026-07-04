import streamlit as st
import pandas as pd
import motor_mestre 

st.set_page_config(
    page_title="MESTRE BLOOMBERG // TELEMETRY_OS",
    page_icon="⚡",
    layout="wide"
)

# CSS Customizado Neon
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

# 🎛️ CONTROLES LATERAIS (SIDEBAR)
with st.sidebar:
    st.markdown('<h2 class="titulo-neon">⚙️ PARÂMETROS DO MOTOR</h2>', unsafe_allow_html=True)
    timeframe_selecionado = st.selectbox("Timeframe (Velas)", ['1m', '5m', '15m', '1h', '4h'], index=2)
    limite_rsi_user = st.slider("Limite RSI (Quarentena)", min_value=50, max_value=90, value=70, step=1)
    distancia_ema_user = st.slider("Distância Máx. EMA (%)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    limite_ema_calc = 1 + (distancia_ema_user / 100)
    
    esquadrao_base = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 
        'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT' 
    ]
    st.write("Ativos monitorados:", len(esquadrao_base))

st.markdown('<h1 class="titulo-neon">⚡ MESTRE BLOOMBERG // TELEMETRY_OS v2.5</h1>', unsafe_allow_html=True)
st.markdown('<div class="status-box">SYSTEM STATUS: OPERACIONAL // RISCO CONTROLADO</div>', unsafe_allow_html=True)
st.write("---")

col_btn, col_espaco = st.columns([1, 4])
with col_btn:
    if st.button("🔄 REBOOT SYNC // ATUALIZAR DADOS", use_container_width=True):
        st.cache_data.clear() 

# Usando st.cache_data para evitar recarregar toda vez que mexer num botão se não for necessário
@st.cache_data(ttl=60) # Faz cache dos dados por 60 segundos
def buscar_dados(tf, rsi, ema):
    return motor_mestre.varredura_global(esquadrao_base, tf, rsi, ema)

with st.spinner(f"Conectando aos satélites da KuCoin ({timeframe_selecionado})..."):
    dados_mercado = buscar_dados(timeframe_selecionado, limite_rsi_user, limite_ema_calc)
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

if not df.empty and 'Preço' in df.columns:
    # Ajuste seguro para pegar o preço do BTC
    linha_btc = df[df['Ativo'] == 'BTC']
    preco_btc = linha_btc.iloc[0]['Preço'] if not linha_btc.empty else "N/A"
else:
    preco_btc = "N/A"

total_quarentena = len(df[df['Veredicto'].str.contains('QUARENTENA')]) if not df.empty else 0

with col1:
    st.metric(label="Rei do Mercado (BTC)", value=preco_btc)
with col2:
    st.metric(label="Ativos em Quarentena", value=f"{total_quarentena} / {len(esquadrao_base)}")
with col3:
    st.metric(label="Circuit Breaker Macro", value="ARMADO", delta="Defesa Ativa")

st.write("---")
st.markdown(f'<h3 class="titulo-neon">📊 RADAR TÁTICO DE EXAUSTÃO ({timeframe_selecionado})</h3>', unsafe_allow_html=True)

st.dataframe(
    df_estilizado,
    use_container_width=True,
    hide_index=True,
    height=400
)

st.markdown("---")
st.markdown("### 🏛️ RELATÓRIO FORENSE INSTITUCIONAL")

data_hora_atual = pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')
ativos_quarentena = df[df['Veredicto'].str.contains('QUARENTENA', na=False)]
ativos_liberados = df[df['Veredicto'].str.contains('LIBERADO', na=False)]

if len(ativos_quarentena) > (len(esquadrao_base) / 2):
    status_mercado = "🔴 ALERTA VERMELHO (Risco Sistêmico Alto - Evitar Entradas)"
elif len(ativos_quarentena) > 0:
    status_mercado = "🟡 ATENÇÃO TÁTICA (Risco Moderado)"
else:
    status_mercado = "🟢 ESTÁVEL (Risco Controlado - Condições Ideais)"

relatorio = f"""
> **DATA DA ANÁLISE:** {data_hora_atual}  
> **DIRETRIZ DE OPERAÇÃO:** {status_mercado}  

**RESUMO EXECUTIVO:** No presente momento, a varredura algorítmica de telemetria analisou a cesta de ativos designada. Constata-se que **{len(ativos_quarentena)}** ativos encontram-se em estado de exceção (Quarentena), devido a anomalias no RSI (> {limite_rsi_user}) ou distanciamento da EMA 20 (> {distancia_ema_user}%), enquanto **{len(ativos_liberados)}** operam dentro dos parâmetros de normalidade e segurança.

**LAUDO DE EXAUSTÃO:**
"""
st.markdown(relatorio)

if not ativos_quarentena.empty:
    for index, row in ativos_quarentena.iterrows():
        st.error(f"⚠️ **Ativo {row['Ativo']} bloqueado.** Motivo detectado: {row['Motivo']}")
else:
    st.success("✅ **Nenhuma anomalia detectada.** Todos os ativos monitorados estão em zona segura para operação.")
