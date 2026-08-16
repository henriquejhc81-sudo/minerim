import time
import ccxt
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# ==========================================
# 1. INICIALIZAÇÃO DE SEGURANÇA
# ==========================================
# Carrega as senhas do arquivo invisível .env (se você estiver rodando local/Codespaces)
load_dotenv()

# Puxa as chaves do ambiente de forma segura
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERRO FATAL: Chaves do Supabase não encontradas.")
    print("Certifique-se de ter criado o arquivo .env com SUPABASE_URL e SUPABASE_KEY.")
    exit()

# Conecta ao Banco de Dados
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Conecta à Corretora (Ex: KuCoin)
exchange = ccxt.kucoin({
    'apiKey': os.getenv("KUCOIN_API_KEY", ""),       
    'secret': os.getenv("KUCOIN_SECRET", ""),        
    'password': os.getenv("KUCOIN_PASSWORD", ""),    
    'enableRateLimit': True,
})

# ==========================================
# 2. NÚCLEO TÁTICO DO EXECUTOR
# ==========================================
def buscar_gatilhos():
    """Lê a tabela do Supabase buscando apenas moedas com status ARMADO."""
    try:
        resposta = supabase.table("gatilhos_operacionais").select("*").eq("status", "ARMADO").execute()
        return resposta.data
    except Exception as e:
        print(f"❌ Erro de conexão com o Supabase: {e}")
        return []

def executar_compra(ativo, preco_compra, take_profit, stop_loss):
    """Atira a ordem na corretora e atualiza o status no banco de dados."""
    print("\n" + "⚡"*20)
    print(f"🚀 ALVO ATINGIDO! EXECUTANDO COMPRA")
    print(f"🛒 Ativo: {ativo}")
    print(f"🎯 Preço de Entrada: ${preco_compra:.4f}")
    print(f"💰 Take Profit Setado: ${take_profit:.4f}")
    print(f"🩸 Stop Loss Setado: ${stop_loss:.4f}")
    print("⚡"*20 + "\n")
    
    # -----------------------------------------------------
    # CÓDIGO DE EXECUÇÃO REAL (KuCoin Limit Order)
    # ATENÇÃO: Só descomente as 3 linhas abaixo quando tiver chaves reais no .env
    # -----------------------------------------------------
    # simbolo_corretora = ativo + '/USDT'
    # tamanho_ordem_usd = 15.0 # Compra fixa de $15 dólares por operação
    # try:
    #     exchange.create_limit_buy_order(simbolo_corretora, tamanho_ordem_usd, preco_compra)
    #     print(f"✅ Ordem real enviada para a corretora: {simbolo_corretora}")
    # except Exception as erro_corretora:
    #     print(f"❌ Falha ao enviar ordem para corretora: {erro_corretora}")
    # -----------------------------------------------------
    
    # Após a ordem ser enviada (ou simulada), avisa o banco que já comprou
    try:
        supabase.table("gatilhos_operacionais").update({"status": "EXECUTADO"}).eq("ativo", ativo).execute()
        print(f"🔄 Banco de dados atualizado. {ativo} marcado como EXECUTADO.")
    except Exception as e:
        print(f"⚠️ Erro ao atualizar status no banco (O robô pode tentar comprar de novo): {e}")

# ==========================================
# 3. LOOP DE ALTA FREQUÊNCIA (RADAR)
# ==========================================
def loop_executor():
    print("\n=========================================")
    print("🤖 EXECUTOR K-NODE INICIADO")
    print("📡 Conectado ao Supabase. Modo de Alta Frequência ativado.")
    print("=========================================\n")
    
    while True:
        try:
            gatilhos = buscar_gatilhos()
            
            if gatilhos:
                for g in gatilhos:
                    ativo = g['ativo']
                    preco_alvo = g['preco_gatilho']
                    
                    # Puxa o preço atualizado no milissegundo exato
                    ticker = exchange.fetch_ticker(ativo + '/USDT')
                    preco_atual = ticker['last']
                    
                    print(f"👀 Vigiando {ativo} | Preço Atual: ${preco_atual:.4f} | Gatilho Alvo: ${preco_alvo:.4f}")
                    
                    # A Mágica Acontece Aqui: Se o preço atual caiu e encostou no gatilho...
                    if preco_atual <= preco_alvo:
                        executar_compra(ativo, preco_alvo, g['take_profit'], g['stop_loss'])
            else:
                print("💤 Nenhum alvo armado pelo Mestre. Varrendo a base...")
                
        except Exception as e:
            print(f"⚠️ Interferência no Radar: {str(e)[:50]}")
            
        # O Executor roda muito mais rápido que o Mestre. Respira 3 segundos e checa de novo.
        time.sleep(3) 

# ==========================================
# START
# ==========================================
if __name__ == "__main__":
    loop_executor()
