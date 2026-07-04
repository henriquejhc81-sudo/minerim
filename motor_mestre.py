import ccxt
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# Conexão com Supabase com tratamento de erro
@st.cache_resource
def conectar_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.warning("Aviso: Credenciais do Supabase não encontradas no st.secrets.")
        return None

supabase = conectar_supabase()

# Instanciando KuCoin com Rate Limit ativado (Evita block da corretora)
exchange = ccxt.kucoin({
    'enableRateLimit': True,
})

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# Agora aceita limites customizáveis via Streamlit
def calcular_indicadores(simbolo, timeframe='15m', limite_rsi=70, limite_ema=1.03):
    try:
        velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=100)
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df['RSI'] = calcular_rsi(df['close'], 14)
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        atual = df.iloc[-1]
        preco = atual['close']
        rsi = atual['RSI']
        ema = atual['EMA_20']
        
        status = "🟢 LIBERADO"
        motivo = "-"
        
        if pd.isna(rsi) or pd.isna(ema):
            status = "⚪ CALCULANDO..."
            motivo = "Aguardando volume"
        elif rsi >= limite_rsi:
            status = "🔴 QUARENTENA"
            motivo = f"RSI >= {limite_rsi} (Sobrecomprado)"
        elif preco > (ema * limite_ema): 
            status = "🔴 QUARENTENA"
            motivo = f"Preço esticado (> {(limite_ema - 1)*100}% da EMA)"

        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço": f"${preco:.4f}",
            "RSI 14": round(rsi, 2),
            "EMA 20": round(ema, 2),
            "Distância EMA": f"{((preco / ema) - 1) * 100:.2f}%",
            "Veredicto": status,
            "Motivo": motivo
        }
        
    except Exception as e:
        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço": "ERRO API",
            "RSI 14": 0.0,
            "EMA 20": 0.0,
            "Distância EMA": "0%",
            "Veredicto": "⚫ FALHA DE CONEXÃO",
            "Motivo": f"Erro: {str(e)[:20]}..."
        }

# Função adaptada para receber parâmetros do Dashboard
def varredura_global(esquadrao, timeframe, limite_rsi, limite_ema):
    resultados = []
    for moeda in esquadrao:
        dados = calcular_indicadores(moeda, timeframe, limite_rsi, limite_ema)
        resultados.append(dados)
    return resultados

# Evolução futura: Função para salvar logs da quarentena no Supabase
def registrar_log_supabase(ativos_quarentena):
    if supabase is not None and not ativos_quarentena.empty:
        # Exemplo de como você vai salvar no futuro:
        # supabase.table("logs_operacionais").insert({"data": datetime.now().isoformat(), "ativos": ativos_quarentena.to_dict()}).execute()
        pass
