import time
import ccxt
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURAÇÕES DE CONEXÃO
# ==========================================
# Insira as mesmas chaves do Supabase que você colocou no Streamlit
SUPABASE_URL = "SUA_URL_DO_SUPABASE"
SUPABASE_KEY = "SUA_CHAVE_ANON_DO_SUPABASE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração da Corretora (Ex: KuCoin)
exchange = ccxt.kucoin({
    'apiKey': 'SUA_API_KEY_DA_CORRETORA',       # Só preencha quando for operar conta real
    'secret': 'SEU_SECRET_DA_CORRETORA',        # Só preencha quando for operar conta real
    'password': 'SUA_PASSWORD_DA_CORRETORA',    # KuCoin exige password da API
    'enableRateLimit': True,
})

# ==========================================
# 2. FUNÇÕES DO EXECUTOR
# ==========================================
def buscar_gatilhos():
    """Lê a tabela do Supabase buscando apenas moedas com status ARMADO."""
    try:
        resposta = supabase.table("gatilhos_operacionais").select("*").eq("status", "ARMADO").execute()
        return resposta.data
    except Exception as e:
        print(f"❌ Erro ao ler Supabase: {e}")
        return []

def executar_compra(ativo, preco_compra, take_profit, stop_loss):
    """Envia a ordem para a corretora e atualiza o banco."""
    print("\n" + "="*40)
    print(f"🚀 ALVO ATINGIDO! EXECUTANDO COMPRA")
    print(f"🛒 Ativo: {ativo}")
    print(f"🎯 Preço de Entrada: ${preco_compra}")
    print(f"💰 Take Profit Setado: ${take_profit}")
    print(f"🩸 Stop Loss Setado: ${stop_loss}")
    print("="*40 + "\n")
    
    # -----------------------------------------------------
    # CÓDIGO DE EXECUÇÃO REAL (DESCOMENTE PARA USAR DINHEIRO REAL)
    # -----------------------------------------------------
    # simbolo_corretora = ativo + '/USDT'
    # tamanho_ordem = 15.0 # Quantidade em USDT que você quer comprar
    # exchange.create_limit_buy_order(simbolo_corretora, tamanho_ordem, preco_compra)
    # -----------------------------------------------------
    
    # Atualiza o status no banco para "EXECUTADO" para o robô não comprar duplicado
    try:
        supabase.table("gatilhos_operacionais").update({"status": "EXECUTADO"}).eq("ativo", ativo).execute()
    except Exception as e:
        print(f"Erro ao atualizar status no banco: {e}")

# ==========================================
# 3. LOOP DE ALTA FREQUÊNCIA
# ==========================================
def loop_executor():
    print("🤖 Robô Executor Iniciado.")
    print("📡 Conectado ao Supabase. Aguardando ordens do Mestre...")
    
    while True:
        try:
            gatilhos = buscar_gatilhos()
            
            if gatilhos:
                for g in gatilhos:
                    ativo = g['ativo']
                    preco_alvo = g['preco_gatilho']
                    
                    # Puxa o preço no milissegundo atual da corretora
                    ticker = exchange.fetch_ticker(ativo + '/USDT')
                    preco_atual = ticker['last']
                    
                    print(f"👀 Vigiando {ativo}: Atual ${preco_atual} | Gatilho ${preco_alvo}")
                    
                    # Se o preço sangrou até o nosso gatilho, ele atira!
                    if preco_atual <= preco_alvo:
                        executar_compra(ativo, preco_alvo, g['take_profit'], g['stop_loss'])
            else:
                print("💤 Nenhum gatilho armado no momento. Aguardando análise do Mestre...")
                
        except Exception as e:
            print(f"⚠️ Erro de rede temporário: {e}")
            
        # O Executor roda muito mais rápido que o Mestre. Ele checa os preços a cada 3 segundos.
        time.sleep(3) 

if __name__ == "__main__":
    loop_executor()
