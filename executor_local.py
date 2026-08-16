import time
import ccxt
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as senhas do arquivo invisível .env
load_dotenv()

# ==========================================
# 1. CONFIGURAÇÕES DE CONEXÃO
# ==========================================
# Agora o código puxa as chaves do ambiente de forma segura
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERRO: Chaves do Supabase não encontradas. Verifique o arquivo .env")
    exit()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração da Corretora (Ex: KuCoin)
exchange = ccxt.kucoin({
    'apiKey': os.getenv("KUCOIN_API_KEY"),       
    'secret': os.getenv("KUCOIN_SECRET"),        
    'password': os.getenv("KUCOIN_PASSWORD"),    
    'enableRateLimit': True,
})

# ... (todo o resto do código da função buscar_gatilhos, executar_compra e loop_executor continua igual) ...
