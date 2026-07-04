import ccxt
import pandas as pd
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()
exchange = ccxt.binance()

# Nova função: Calcula o RSI nativamente sem depender do pandas-ta
def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calcular_indicadores(simbolo, timeframe='15m'):
    try:
        velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=100)
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculando RSI e EMA usando pandas puro!
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
        elif rsi >= 70:
            status = "🔴 QUARENTENA"
            motivo = "RSI > 70 (Sobrecomprado)"
        elif preco > (ema * 1.03): 
            status = "🔴 QUARENTENA"
            motivo = "Preço esticado (>3% da EMA)"

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
            "Motivo": "A Binance recusou a leitura"
        }

def varredura_global():
    esquadrao = [
        'BTC/USDT', 'ETH/USDT', 
        'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT',
        'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT' 
    ]
    
    resultados = []
    for moeda in esquadrao:
        dados = calcular_indicadores(moeda, timeframe='15m')
        resultados.append(dados)
        
    return resultados
