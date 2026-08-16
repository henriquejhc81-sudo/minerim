import ccxt
import pandas as pd
import streamlit as st

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
    # Retorna: Grupo, Limite RSI, Limite EMA, Fator de Queda (Sangramento esperado)
    if simbolo in ['BTC/USDT', 'ETH/USDT']:
        return 'Alta Liquidez', 75, 1.025, 0.0070  # Espera queda de -0.70% para gatilho
    elif simbolo in ['AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']:
        return 'Alta Vol.', 85, 1.050, 0.0150      # Espera queda de -1.50% para gatilho
    else:
        return 'Média Vol.', 80, 1.035, 0.0100     # Espera queda de -1.00% para gatilho

def buscar_fechamento(simbolo, timeframe):
    """Função auxiliar para buscar apenas o preço de fechamento de um TF específico."""
    velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=20)
    df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    ultima_vela = df.iloc[-1]
    return ultima_vela['close'], ultima_vela['EMA_20']

def analise_autobolt(simbolo):
    try:
        grupo, limite_rsi, limite_ema, fator_queda = classificar_ativo(simbolo)
        
        # 1. ANÁLISE MULTI-TIMEFRAME (2h, 4h, 6h, 12h)
        # O objetivo é verificar se todos os tempos gráficos maiores estão apontando para cima
        preco_2h, ema_2h = buscar_fechamento(simbolo, '2h')
        preco_4h, ema_4h = buscar_fechamento(simbolo, '4h')
        preco_6h, ema_6h = buscar_fechamento(simbolo, '6h')
        preco_12h, ema_12h = buscar_fechamento(simbolo, '12h')
        
        # Calcula Força Institucional (Quantos TFs estão em tendência de alta?)
        score_alta = 0
        if preco_2h > ema_2h: score_alta += 1
        if preco_4h > ema_4h: score_alta += 1
        if preco_6h > ema_6h: score_alta += 1
        if preco_12h > ema_12h: score_alta += 1
        
        # 2. ANÁLISE MICRO PARA ENTRADA (15m)
        velas_15m = exchange.fetch_ohlcv(simbolo, '15m', limit=100)
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m['RSI'] = calcular_rsi(df_15m['close'], 14)
        df_15m['EMA_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
        
        atual = df_15m.iloc[-1]
        preco_atual = atual['close']
        rsi = atual['RSI']
        ema_micro = atual['EMA_20']
        
        # 3. CÁLCULO DO GATILHO DINÂMICO
        # Se a tendência macro for muito forte (score 4), compramos num recuo menor.
        # Se for mais fraca, esperamos sangrar mais para ter segurança.
        ajuste_forca = (4 - score_alta) * 0.002 # Adiciona 0.2% de sangramento exigido para cada TF que não estiver em alta
        queda_alvo = fator_queda + ajuste_forca
        
        preco_gatilho = preco_atual * (1 - queda_alvo)
        
        status = "🟢 GATILHO ARMADO"
        motivo = f"Tendência validada em {score_alta}/4 TFs."
        
        # 4. AS TRAVAS DE SEGURANÇA
        if score_alta < 2:
            status = "🟠 BLOQUEIO MACRO"
            motivo = "Rejeição: Tendência de Baixa nos TFs maiores."
            preco_gatilho = 0.0 # Zera o gatilho para o robô executor ignorar
            
        elif pd.isna(rsi) or pd.isna(ema_micro):
            status = "⚪ CALCULANDO..."
            motivo = "Aguardando volume histórico."
            preco_gatilho = 0.0
            
        elif rsi >= limite_rsi:
            status = "🔴 QUARENTENA"
            motivo = f"RSI Micro >= {limite_rsi} (Risco de Correção Forte)."
            preco_gatilho = 0.0
            
        elif preco_atual > (ema_micro * limite_ema): 
            status = "🔴 QUARENTENA"
            motivo = f"Preço muito esticado da média."
            preco_gatilho = 0.0

        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço Atual": f"${preco_atual:.4f}",
            "Score Macro": f"{score_alta}/4 Alta",
            "Gatilho Executor": f"${preco_gatilho:.4f}" if preco_gatilho > 0 else "AGUARDAR",
            "Alvo Queda": f"-{(queda_alvo * 100):.2f}%",
            "Veredicto": status,
            "Motivo": motivo
        }
        
    except Exception as e:
        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço Atual": "ERRO API",
            "Score Macro": "0/4",
            "Gatilho Executor": "FALHA",
            "Alvo Queda": "N/A",
            "Veredicto": "⚫ FALHA DE REDE",
            "Motivo": str(e)[:30]
        }

def varredura_global():
    esquadrao = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 
        'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT'
    ]
    resultados = [analise_autobolt(moeda) for moeda in esquadrao]
    return resultados
