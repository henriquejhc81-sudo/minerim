import ccxt
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz

tz_br = pytz.timezone('America/Sao_Paulo')

@st.cache_resource
def iniciar_exchange():
    return ccxt.kucoin({'enableRateLimit': True})

exchange = iniciar_exchange()

# ==========================================
# MEMÓRIA DO SIMULADOR (PAPER TRADING)
# ==========================================
@st.cache_resource
def get_simulador_state():
    return {
        'gatilhos': {},       # Guarda os gatilhos armados: {moeda: preco_gatilho}
        'posicoes': {},       # Operações em andamento: {moeda: {entrada, tp, sl, hora}}
        'historico': [],      # Lista de operações fechadas
        'saldo_virtual': 10000.0, # Começa com uma banca fictícia de 10 mil dólares
        'pnl_total': 0.0      # Rendimento Total em %
    }

# ==========================================
# CÁLCULOS MATEMÁTICOS E CLASSIFICAÇÃO
# ==========================================
def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def classificar_ativo(simbolo):
    if simbolo in ['BTC/USDT', 'ETH/USDT']: return 'Alta Liquidez', 75, 1.025, 0.0070
    elif simbolo in ['AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']: return 'Alta Vol.', 85, 1.050, 0.0150
    else: return 'Média Vol.', 80, 1.035, 0.0100

def buscar_fechamento(simbolo, timeframe):
    velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=20)
    df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    ultima_vela = df.iloc[-1]
    return ultima_vela['close'], ultima_vela['EMA_20']

def analise_autobolt(simbolo):
    try:
        grupo, limite_rsi, limite_ema, fator_queda = classificar_ativo(simbolo)
        
        # 1. ANÁLISE MACRO
        preco_2h, ema_2h = buscar_fechamento(simbolo, '2h')
        preco_4h, ema_4h = buscar_fechamento(simbolo, '4h')
        preco_6h, ema_6h = buscar_fechamento(simbolo, '6h')
        preco_12h, ema_12h = buscar_fechamento(simbolo, '12h')
        
        score_alta = sum([preco_2h > ema_2h, preco_4h > ema_4h, preco_6h > ema_6h, preco_12h > ema_12h])
        
        # 2. ANÁLISE MICRO
        velas_15m = exchange.fetch_ohlcv(simbolo, '15m', limit=100)
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m['RSI'] = calcular_rsi(df_15m['close'], 14)
        df_15m['EMA_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
        
        atual = df_15m.iloc[-1]
        preco_atual = atual['close']
        rsi = atual['RSI']
        ema_micro = atual['EMA_20']
        
        # 3. GATILHO
        ajuste_forca = (4 - score_alta) * 0.002
        queda_alvo = fator_queda + ajuste_forca
        preco_gatilho = preco_atual * (1 - queda_alvo)
        
        status, motivo = "🟢 GATILHO ARMADO", f"Tendência em {score_alta}/4 TFs."
        
        # 4. TRAVAS
        if score_alta < 2:
            status, motivo, preco_gatilho = "🟠 BLOQUEIO MACRO", "Rejeição: Tendência de Baixa Macro.", 0.0
        elif pd.isna(rsi) or pd.isna(ema_micro):
            status, motivo, preco_gatilho = "⚪ CALCULANDO...", "Aguardando volume.", 0.0
        elif rsi >= limite_rsi:
            status, motivo, preco_gatilho = "🔴 QUARENTENA", f"RSI Topo >= {limite_rsi}.", 0.0
        elif preco_atual > (ema_micro * limite_ema): 
            status, motivo, preco_gatilho = "🔴 QUARENTENA", "Preço esticado.", 0.0

        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço Atual": f"${preco_atual:.4f}",
            "Score Macro": f"{score_alta}/4 Alta",
            "Gatilho Executor": f"${preco_gatilho:.4f}" if preco_gatilho > 0 else "AGUARDAR",
            "Alvo Queda": f"-{(queda_alvo * 100):.2f}%",
            "Veredicto": status,
            "Motivo": motivo,
            "_raw_preco": preco_atual # Usado internamente pelo simulador
        }
    except Exception as e:
        return {"Ativo": simbolo.replace('/USDT', ''), "Preço Atual": "ERRO API", "Score Macro": "0/4", "Gatilho Executor": "FALHA", "Alvo Queda": "N/A", "Veredicto": "⚫ FALHA", "Motivo": "Erro", "_raw_preco": 0}

# ==========================================
# NÚCLEO DO SIMULADOR INSTITUCIONAL
# ==========================================
def gerenciar_simulador(resultados):
    sim = get_simulador_state()
    
    for res in resultados:
        simbolo = res['Ativo']
        preco_atual = res['_raw_preco']
        
        if preco_atual == 0: continue
        
        # 1. VERIFICA POSIÇÕES EM ANDAMENTO (TAKE PROFIT OU STOP LOSS)
        if simbolo in sim['posicoes']:
            pos = sim['posicoes'][simbolo]
            
            if preco_atual >= pos['tp']: # Bateu no lucro
                lucro_pct = (pos['tp'] / pos['entrada']) - 1
                lucro_usd = (sim['saldo_virtual'] * 0.10) * lucro_pct # Risco de 10% da banca por trade
                sim['saldo_virtual'] += lucro_usd
                sim['pnl_total'] += lucro_pct * 100
                sim['historico'].insert(0, {'Ativo': simbolo, 'Resultado': '✅ WIN', 'Entrada': f"${pos['entrada']:.4f}", 'Saída': f"${pos['tp']:.4f}", 'Lucro/Perda': f"+{lucro_pct*100:.2f}%", 'Data': datetime.now(tz_br).strftime('%d/%m %H:%M')})
                del sim['posicoes'][simbolo]
                
            elif preco_atual <= pos['sl']: # Bateu no loss
                perda_pct = 1 - (pos['sl'] / pos['entrada'])
                perda_usd = (sim['saldo_virtual'] * 0.10) * perda_pct
                sim['saldo_virtual'] -= perda_usd
                sim['pnl_total'] -= perda_pct * 100
                sim['historico'].insert(0, {'Ativo': simbolo, 'Resultado': '❌ LOSS', 'Entrada': f"${pos['entrada']:.4f}", 'Saída': f"${pos['sl']:.4f}", 'Lucro/Perda': f"-{perda_pct*100:.2f}%", 'Data': datetime.now(tz_br).strftime('%d/%m %H:%M')})
                del sim['posicoes'][simbolo]
                
        # 2. VERIFICA NOVAS COMPRAS SE O GATILHO FOI ATINGIDO
        else:
            if simbolo in sim['gatilhos'] and preco_atual <= sim['gatilhos'][simbolo]:
                # Compra Efetuada! Define Alvos (3% Lucro, 1.5% Risco)
                preco_compra = sim['gatilhos'][simbolo]
                sim['posicoes'][simbolo] = {
                    'entrada': preco_compra,
                    'tp': preco_compra * 1.03,
                    'sl': preco_compra * 0.985,
                    'hora': datetime.now(tz_br).strftime('%H:%M:%S')
                }
                del sim['gatilhos'][simbolo]
                
            elif "QUARENTENA" in res['Veredicto'] or "BLOQUEIO" in res['Veredicto']:
                # Cenário piorou, remove o gatilho da memória
                if simbolo in sim['gatilhos']: del sim['gatilhos'][simbolo]
                
            elif "$" in res['Gatilho Executor']:
                # Arma/Atualiza o gatilho na memória
                preco_alvo = float(res['Gatilho Executor'].replace('$', ''))
                sim['gatilhos'][simbolo] = preco_alvo

def varredura_global():
    esquadrao = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']
    resultados = [analise_autobolt(moeda) for moeda in esquadrao]
    gerenciar_simulador(resultados) # Atualiza o Paper Trading silenciosamente
    return resultados
