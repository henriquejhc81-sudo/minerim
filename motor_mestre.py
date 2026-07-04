import ccxt
import pandas as pd
import streamlit as st

# Conexão com a KuCoin
@st.cache_resource
def iniciar_exchange():
    return ccxt.kucoin({'enableRateLimit': True})

exchange = iniciar_exchange()

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def classificar_ativo(simbolo):
    """Autobolt: Define parâmetros dinâmicos baseados no grupo de volatilidade."""
    if simbolo in ['BTC/USDT', 'ETH/USDT']:
        return 'Alta Liquidez', 75, 1.025  # Tolera menos esticamento
    elif simbolo in ['AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']:
        return 'Alta Vol.', 85, 1.050      # Tolera mais volatilidade
    else:
        return 'Média Vol.', 80, 1.035     # Padrão para BNB, SOL, etc.

def analise_autobolt(simbolo):
    """Analisa múltiplos tempos gráficos e aplica as 3 Travas."""
    try:
        grupo, limite_rsi, limite_ema = classificar_ativo(simbolo)
        
        # Busca dados Macro (4h) e Micro (15m)
        velas_4h = exchange.fetch_ohlcv(simbolo, '4h', limit=200)
        velas_15m = exchange.fetch_ohlcv(simbolo, '15m', limit=100)
        
        df_4h = pd.DataFrame(velas_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Cálculos Micro (15m)
        df_15m['RSI'] = calcular_rsi(df_15m['close'], 14)
        df_15m['EMA_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
        
        # Cálculos Macro (4h) - Média de 200 para Tendência
        df_4h['EMA_200'] = df_4h['close'].ewm(span=200, adjust=False).mean()
        
        atual = df_15m.iloc[-1]
        macro_atual = df_4h.iloc[-1]
        
        preco = atual['close']
        rsi = atual['RSI']
        ema_20 = atual['EMA_20']
        ema_200_macro = macro_atual['EMA_200']
        
        status = "🟢 LIBERADO"
        motivo = "Tendência de Alta & Sem Exaustão"
        
        # As 3 Travas do Autobolt
        if pd.isna(rsi) or pd.isna(ema_20):
            status = "⚪ CALCULANDO..."
            motivo = "Aguardando volume histórico"
            
        elif preco < ema_200_macro:
            status = "🟠 BLOQUEIO MACRO"
            motivo = "Tendência de Baixa no Gráfico 4h"
            
        elif rsi >= limite_rsi:
            status = "🔴 QUARENTENA"
            motivo = f"RSI Micro >= {limite_rsi} (Topo)"
            
        elif preco > (ema_20 * limite_ema): 
            status = "🔴 QUARENTENA"
            motivo = f"Preço esticado (> {(limite_ema - 1)*100:.1f}% da EMA)"

        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Grupo": grupo,
            "Preço": f"${preco:.4f}",
            "RSI 14 (Micro)": round(rsi, 2),
            "Distância EMA": f"{((preco / ema_20) - 1) * 100:.2f}%",
            "Veredicto": status,
            "Motivo": motivo
        }
        
    except Exception as e:
        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Grupo": "Desconhecido",
            "Preço": "ERRO API",
            "RSI 14 (Micro)": 0.0,
            "Distância EMA": "0%",
            "Veredicto": "⚫ FALHA",
            "Motivo": "Erro de conexão com corretora"
        }

def varredura_global():
    esquadrao = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 
        'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT'
    ]
    resultados = [analise_autobolt(moeda) for moeda in esquadrao]
    return resultados
