"""
Script de RPA para extração de clientes e envio para Webhook do n8n.
Projeto: Assistente de Investimentos com RPA e n8n.
"""

import sys
import json
import argparse
import urllib.request
from bs4 import BeautifulSoup


URL_PAGINA_PADRAO = "https://digitalinnovationone.github.io/dio-lab-assistente-investimentos-rpa-n8n/"


def extrair_clientes(url=URL_PAGINA_PADRAO):
    """
    Acessa a página HTML de clientes e extrai os dados da tabela via BeautifulSoup.
    """
    print(f"[*] Acessando pagina: {url}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DIO-RPA-Bot/1.0"}
    )
    
    with urllib.request.urlopen(req) as response:
        html = response.read().decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")
    linhas = soup.select("#clientes tbody tr")

    clientes = []
    for linha in linhas:
        colunas = linha.find_all("td")
        if len(colunas) >= 4:
            cliente = {
                "nome": colunas[0].get_text(strip=True),
                "email": colunas[1].get_text(strip=True),
                "saldo": colunas[2].get_text(strip=True),
                "perfil": colunas[3].get_text(strip=True),
            }
            clientes.append(cliente)

    return clientes


def enviar_n8n(webhook_url, clientes, csv_url=None):
    """
    Envia a lista de clientes extraída para o webhook do n8n via requisição POST JSON.
    Permite passar opcionalmente uma URL personalizada para o arquivo CSV de investimentos.
    """
    print(f"[*] Enviando {len(clientes)} clientes para o Webhook do n8n: {webhook_url}")
    corpo = {"clientes": clientes}
    if csv_url:
        print(f"[*] Especificando URL customizada do CSV: {csv_url}")
        corpo["csv_url"] = csv_url

    payload = json.dumps(corpo).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DIO-RPA-Client/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            resposta_corpo = resp.read().decode("utf-8")
            print(f"[+] Sucesso! Status HTTP {status}")
            try:
                resposta_json = json.loads(resposta_corpo)
                print("[+] Resposta do n8n:\n", json.dumps(resposta_json, indent=2, ensure_ascii=False))
            except Exception:
                print("[+] Resposta em texto puro do n8n:\n", resposta_corpo)
    except Exception as e:
        print(f"[-] Erro ao enviar para o webhook do n8n: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Extrai clientes via RPA e envia para o workflow n8n.")
    parser.add_argument("--url", default=URL_PAGINA_PADRAO, help="URL da página de clientes")
    parser.add_argument("--webhook", default=None, help="URL do Webhook do n8n (ex: http://localhost:5678/webhook/clientes)")
    parser.add_argument("--csv-url", default=None, help="URL customizada para o CSV de investimentos (opcional)")
    parser.add_argument("--local", action="store_true", help="Usar arquivo local docs/index.html em vez da URL web")
    args = parser.parse_args()

    if args.local:
        print("[*] Lendo arquivo local docs/index.html...")
        with open("docs/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        linhas = soup.select("#clientes tbody tr")
        clientes = []
        for linha in linhas:
            colunas = linha.find_all("td")
            if len(colunas) >= 4:
                clientes.append({
                    "nome": colunas[0].get_text(strip=True),
                    "email": colunas[1].get_text(strip=True),
                    "saldo": colunas[2].get_text(strip=True),
                    "perfil": colunas[3].get_text(strip=True),
                })
    else:
        clientes = extrair_clientes(args.url)

    print(f"\n[+] Total de {len(clientes)} clientes extraidos:")
    print("-" * 70)
    for c in clientes:
        print(f" - {c['nome']:<18} | {c['email']:<20} | {c['saldo']:<14} | {c['perfil']}")
    print("-" * 70)

    if args.webhook:
        enviar_n8n(args.webhook, clientes, args.csv_url)
    else:
        print("\n[i] Para enviar ao n8n, execute informando a URL do webhook:")
        print("    python rpa/extrair_clientes.py --webhook http://localhost:5678/webhook-test/clientes")


if __name__ == "__main__":
    main()
