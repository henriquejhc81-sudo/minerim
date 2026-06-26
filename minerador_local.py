import subprocess
import time
import re
import os
from supabase import create_client, Client

# --- CONFIGURAÇÕES DO BANCO ---
SUPABASE_URL = "SUA_URL_DO_SUPABASE"
SUPABASE_KEY = "SUA_CHAVE_DO_SUPABASE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def ler_comando_remoto():
    """Lê o banco para saber se o Streamlit mandou parar a máquina"""
    try:
        resposta = supabase.table("status_rig").select("comando_status").order("id", desc=True).limit(1).execute()
        if resposta.data:
            return resposta.data[0]['comando_status']
    except Exception as e:
        print(f"Erro ao ler banco: {e}")
    return "rodar"

def atualizar_banco(hashrate, temp):
    """Envia os dados de mineração para o painel"""
    try:
        supabase.table("status_rig").insert({
            "hashrate": hashrate,
            "temperatura": temp,
            "comando_status": "rodar"
        }).execute()
    except Exception as e:
        print(f"Erro ao enviar dados: {e}")

def iniciar_mineracao():
    print("🚀 Iniciando Rig de Mineração...")
    
    # Altere para a sua carteira e pool
    comando = [
        "./xmrig", # no Windows use "xmrig.exe"
        "-o", "pool.supportxmr.com:443", 
        "-u", "48s23TPdvDm52aEqj2a6Ny1Dh4ejFgrpgKEgAKmKaZmm1soHn42DUioGqV3hzNc5Hgj26fy8AFZf76aFaddWnvZuUL9wcek", 
        "-p", "Rig01",
        "--tls"
    ]
    
    processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    ultimo_envio = time.time()
    hashrate_atual = "0 H/s"
    temp_atual = "0 °C"

    try:
        while True:
            # 1. Verifica se recebemos ordem para parar
            if ler_comando_remoto() == "parar":
                print("🛑 Comando de parada recebido do painel! Desligando...")
                processo.terminate()
                break

            # 2. Lê a saída do XMRig no terminal
            linha = processo.stdout.readline()
            if not linha and processo.poll() is not None:
                break
            
            # Limpa códigos de cor do terminal para facilitar a leitura
            linha_limpa = re.sub(r'\x1b\[[0-9;]*m', '', linha)

            # 3. Captura Hashrate e Temperatura via Regex
            if "speed" in linha_limpa or "max" in linha_limpa:
                # Exemplo de linha do XMRig: [2023-10-25] speed 10s/60s/15m 1450.5 1445.2 1440.1 H/s max 1500.0 H/s
                match_hash = re.search(r'max\s+([0-9.]+)\s+H/s', linha_limpa)
                if match_hash:
                    hashrate_atual = f"{match_hash.group(1)} H/s"
                    print(f"⚡ Hashrate detectado: {hashrate_atual}")

            # Nota: O XMRig nem sempre mostra a temperatura nativamente sem ser via API ou privilégios de admin.
            # Aqui simulamos a captura caso a flag print-time mostre.
            if "cpu" in linha_limpa.lower() and "°C" in linha_limpa:
                 match_temp = re.search(r'([0-9]+)\s*°C', linha_limpa)
                 if match_temp:
                     temp_atual = f"{match_temp.group(1)} °C"

            # 4. Envia para o banco a cada 10 segundos
            if time.time() - ultimo_envio > 10:
                print(f"📡 Enviando telemetria: {hashrate_atual} | {temp_atual}")
                atualizar_banco(hashrate_atual, temp_atual)
                ultimo_envio = time.time()

    except KeyboardInterrupt:
        print("Desligamento manual...")
        processo.terminate()

if __name__ == "__main__":
    iniciar_mineracao()
