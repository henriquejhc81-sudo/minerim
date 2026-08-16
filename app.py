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
    .header-box {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 20px;
    }
    .titulo { color: #ffffff; font-weight: 800; font-family: 'Inter', sans-serif; margin: 0; }
    .subtitulo { color: #94a3b8; font-family: 'Inter', monospace; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-box">
        <h1 class="titulo">⚡ AUTOBOLT ENGINE v3.5</h1>
        <div class="subtitulo">SISTEMA AUTÔNOMO DE PROTEÇÃO CONTRA TOPOS // MULTI-TIMEFRAME & GATILHOS DE EXECUÇÃO</div>
    </div>
""", unsafe_allow_html=True)

col_btn, col_espaco = st.columns([1, 4])
with col_btn:
    if st.button("🔄 FORÇAR VARREDURA DA IA", use_container_width=True):
        st.cache_data.clear() 

@st.cache_data(ttl=120) 
def buscar_dados_inteligentes():
    return motor_mestre.varredura_global()

with st.spinner("Analisando fractais de 2h, 4h, 6h, 12h e calculando sangramento ideal..."):
    dados_mercado = buscar_dados_inteligentes()
    df = pd.DataFrame(dados_mercado)

# Colorização Inteligente
def colorir_tabela(val):
    val_str = str(val)
    if "GATILHO ARMADO" in val_str: return 'color: #10b981; font-weight: bold;'
    elif "QUARENTENA" in val_str: return 'color: #ef4444; font-weight: bold;'
    elif "BLOQUEIO" in val_str: return 'color: #f59e0b; font-weight: bold;'
    elif "$" in val_str and val_str != "AGUARDAR" and val_str != "FALHA": return 'color: #38bdf8; font-weight: bold;' # Destaca o preço gatilho em azul neon
    return 'color: #94a3b8;'

df_estilizado = df.style.map(colorir_tabela)

# KPIs Institucionais
st.write("---")
col1, col2, col3, col4 = st.columns(4)

liberados = len(df[df['Veredicto'].str.contains('GATILHO ARMADO')]) if not df.empty else 0
quarentena = len(df[df['Veredicto'].str.contains('QUARENTENA')]) if not df.empty else 0
bloqueados = len(df[df['Veredicto'].str.contains('BLOQUEIO')]) if not df.empty else 0

with col1: st.metric("Ativos Totais", len(df))
with col2: st.metric("Gatilhos Armados", liberados)
with col3: st.metric("Risco de Topo (Quarentena)", quarentena)
with col4: st.metric("Queda Macro (Bloqueados)", bloqueados)

st.write("---")
st.markdown('### 📡 MATRIX DE DECISÃO AUTÔNOMA E GATILHOS')

st.dataframe(
    df_estilizado,
    use_container_width=True,
    hide_index=True,
    height=420
)

st.write("---")
st.markdown("### 🧠 LOG DE PENSAMENTO DA IA")
for index, row in df.iterrows():
    if "GATILHO ARMADO" in row['Veredicto']:
        st.caption(f"- 🟢 **{row['Ativo']}:** Tendência forte ({row['Score Macro']}). Aguardando sangramento de {row['Alvo Queda']} para comprar em {row['Gatilho Executor']}.")
    elif "QUARENTENA" in row['Veredicto'] or "BLOQUEIO" in row['Veredicto']:
        st.caption(f"- 🛑 **{row['Ativo']}:** Protegido. Motivo: {row['Motivo']}")
