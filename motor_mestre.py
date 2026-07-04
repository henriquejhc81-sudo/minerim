import ccxt
import pandas as pd
import pandas_ta as ta
import streamlit as st
from supabase import create_client, Client

# 1. Configuração da Conexão com o Supabase (lendo as chaves seguras)
@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# 2. Inicializando a Binance (Modo Público, sem necessidade de API Key)
exchange = ccxt.binance()

def calcular_indicadores(simbolo, timeframe='15m'):
    """
    Função tática: Vai até a Binance, pega os dados e calcula a matemática pesada.
    """
    try:
        # Puxa 100 candles de histórico
        velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=100)
        
        # Converte para uma tabela (DataFrame) do Pandas para facilitar o cálculo
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # A mágica do pandas_ta: Calcula RSI e Médias com uma linha de código
        df['RSI'] = df.ta.rsi(length=14)
        df['EMA_20'] = df.ta.ema(length=20)
        
        # Isola a última linha (o milissegundo atual do mercado)
        atual = df.iloc[-1]
        
        preco = atual['close']
        rsi = atual['RSI']
        ema = atual['EMA_20']
        
        # 3. O Escudo Anti-Topo (Definição de Quarentena)
        status = "🟢 LIBERADO"
        motivo = "-"
        
        if pd.isna(rsi) or pd.isna(ema):
            status = "⚪ CALCULANDO..."
            motivo = "Aguardando volume"
            
        elif rsi >= 70:
            status = "🔴 QUARENTENA"
            motivo = "RSI > 70 (Sobrecomprado)"
            
        elif preco > (ema * 1.03): # Se o preço estiver mais de 3% longe da média de 20
            status = "🔴 QUARENTENA"
            motivo = "Preço esticado (>3% da EMA)"

        return {
            "Ativo": simbolo.replace('/USDT', ''), # Limpa o nome para ficar bonito no painel
            "Preço": f"${preco:.4f}",
            "RSI 14": round(rsi, 2),
            "EMA 20": round(ema, 2),
            "Distância EMA": f"{((preco / ema) - 1) * 100:.2f}%",
            "Veredicto": status,
            "Motivo": motivo
        }
        
    except Exception as e:
        return {"Ativo": simbolo, "Veredicto": f"ERRO: {e}"}

def varredura_global():
    """
    O Mestre operando: Varre os 3 esquadrões de moedas.
    """
    esquadrao = [
        'BTC/USDT', 'ETH/USDT', # G1: Macro
        'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', # G2: Ecossistemas
        'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT' # G3: Explosivas
    ]
    
    resultados = []
    for moeda in esquadrao:
        dados = calcular_indicadores(moeda, timeframe='15m')
        resultados.append(dados)
        
    return resultados
