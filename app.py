import streamlit as st
import pandas as pd
import motor_mestre 

st.set_page_config(
    page_title="AUTOBOLT OS // INSTITUCIONAL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .header-box { background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 20px; }
    .titulo { color: #ffffff; font-weight: 900; font-family: 'Inter', sans-serif; margin: 0; }
    .subtitulo { color: #94a3b8; font-family: 'Inter', monospace; margin-top: 5px; }
    
    /* Estilização das Abas (Tabs) do Streamlit */
    div[data-testid="stTabs"] button { font-weight: bold; font-size: 16px; color: #94a3b8; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #3b82f6 !important; border-bottom-color: #3b82f6 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-box">
        <h1 class="titulo">⚡ AUTOBOLT ENGINE v4.0</h1>
        <div class="subtitulo">MOTOR MULTI-TIMEFRAME & SIMULADOR DE EXECUÇÃO ALGORÍTMICA</div>
    </div>
""", unsafe_allow_html=True)

col_btn, col_espaco = st.columns([1, 4])
with col_btn:
    if st.button("🔄 FORÇAR VARREDURA DA IA", use_container_width=True):
        st.cache_data.clear() 

@st.cache_data(ttl=120) 
def buscar_dados_inteligentes():
    return motor_mestre.varredura_global()

with st.spinner("Sincronizando fractais e processando simulações no motor K-Node..."):
    dados_mercado = buscar_dados_inteligentes()
    df = pd.DataFrame(dados_mercado).drop(columns=['_raw_preco'], errors='ignore') # Esconde o dado bruto

# CRIANDO AS ABAS
aba_matriz, aba_simulador = st.tabs(["📡 MATRIX DE DECISÃO", "🕹️ SIMULADOR DE OPERAÇÕES"])

# ==========================================
# ABA 1: MATRIX DE DECISÃO (Painel Original)
# ==========================================
with aba_matriz:
    def colorir_tabela(val):
        val_str = str(val)
        if "GATILHO ARMADO" in val_str: return 'color: #10b981; font-weight: bold;'
        elif "QUARENTENA" in val_str: return 'color: #ef4444; font-weight: bold;'
        elif "BLOQUEIO" in val_str: return 'color: #f59e0b; font-weight: bold;'
        elif "$" in val_str and val_str not in ["AGUARDAR", "FALHA"]: return 'color: #38bdf8; font-weight: bold;' 
        return 'color: #94a3b8;'

    df_estilizado = df.style.map(colorir_tabela)

    st.write("---")
    c1, c2, c3, c4 = st.columns(4)
    liberados = len(df[df['Veredicto'].str.contains('GATILHO ARMADO')]) if not df.empty else 0
    quarentena = len(df[df['Veredicto'].str.contains('QUARENTENA')]) if not df.empty else 0
    bloqueados = len(df[df['Veredicto'].str.contains('BLOQUEIO')]) if not df.empty else 0

    with c1: st.metric("Ativos Totais", len(df))
    with c2: st.metric("Gatilhos Armados", liberados)
    with c3: st.metric("Risco de Topo", quarentena)
    with c4: st.metric("Queda Macro", bloqueados)

    st.write("---")
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True, height=420)

# ==========================================
# ABA 2: SIMULADOR DE EXECUÇÃO (Paper Trading)
# ==========================================
with aba_simulador:
    # Resgata o estado atualizado da memória do motor
    sim_state = motor_mestre.get_simulador_state()
    
    st.markdown("### 📊 DASHBOARD FINANCEIRO VIRTUAL")
    c_s1, c_s2, c_s3, c_s4 = st.columns(4)
    
    # Renderiza KPIs
    with c_s1: st.metric("Banca Simulada", f"${sim_state['saldo_virtual']:,.2f}")
    with c_s2: st.metric("Desempenho Geral (PNL)", f"{sim_state['pnl_total']:+.2f}%")
    with c_s3: st.metric("Posições Abertas (Real-Time)", len(sim_state['posicoes']))
    with c_s4: st.metric("Trades Fechados", len(sim_state['historico']))
    
    st.write("---")
    st.markdown("### 🛒 CAIXA DE OPERAÇÕES EM ANDAMENTO")
    
    if sim_state['posicoes']:
        df_pos = pd.DataFrame([
            {'Ativo': k, 'Hora Entrada': v['hora'], 'Preço Médio (Entrada)': f"${v['entrada']:.4f}", 'Alvo (Take Profit)': f"${v['tp']:.4f}", 'Stop Loss': f"${v['sl']:.4f}"}
            for k, v in sim_state['posicoes'].items()
        ])
        st.dataframe(df_pos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma operação em andamento no momento. Os robôs estão aguardando o preço sangrar até o gatilho para executar a compra.")
        
    st.write("---")
    st.markdown("### 📜 HISTÓRICO DE TRADES (LOG DE AUDITORIA)")
    
    if sim_state['historico']:
        df_hist = pd.DataFrame(sim_state['historico'])
        def colorir_hist(val):
            if "WIN" in str(val) or "+" in str(val): return 'color: #10b981; font-weight: bold;'
            elif "LOSS" in str(val) or "-" in str(val): return 'color: #ef4444; font-weight: bold;'
            return ''
        st.dataframe(df_hist.style.map(colorir_hist), use_container_width=True, hide_index=True)
    else:
        st.caption("Quando uma operação atingir o alvo ou o stop loss, o resultado aparecerá aqui.")
