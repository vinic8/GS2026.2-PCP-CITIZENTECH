"""Citizen Assist AI - assistente de orientação ao cidadão.

Público atendido: jovens de 16 a 24 anos entrando no primeiro emprego.
Rode com: python main.py
"""

import os

from assistente import Assistente
from base_conhecimento import BaseConhecimento

# Caminhos relativos ao arquivo, não à pasta de onde o programa foi chamado.
RAIZ = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE = os.path.join(RAIZ, "data", "base_conhecimento.json")
CAMINHO_HISTORICO = os.path.join(RAIZ, "data", "historico.json")
CAMINHO_CSV = os.path.join(RAIZ, "data", "atendimentos.csv")

NOME = "Citizen Assist AI"


def mostrar_menu():
    print("\n==========================================")
    print(f" {NOME}")
    print(" Orientação para o primeiro emprego")
    print("==========================================")
    print("  1. Tirar uma dúvida (digitando a pergunta)")
    print("  2. Navegar por categorias")
    print("  3. Ver indicadores")
    print("  0. Sair")


def main():
    base = BaseConhecimento(CAMINHO_BASE)
    if not base.carregar():
        print("\nNão foi possível iniciar o assistente.")
        print("Corrija o arquivo da base de conhecimento e tente de novo.")
        return

    assistente = Assistente(NOME, base, CAMINHO_HISTORICO, CAMINHO_CSV)

    print(f"\n{len(base.orientacoes)} orientações carregadas "
          f"em {len(base.categorias())} categorias.")
    print("Este assistente NÃO é um canal oficial e nunca pede seus dados pessoais.")

    while True:
        mostrar_menu()
        escolha = input("Escolha uma opção: ").strip()

        if escolha == "1":
            assistente.perguntar()
        elif escolha == "2":
            assistente.navegar()
        elif escolha == "3":
            assistente.indicadores()
        elif escolha == "0":
            assistente.encerrar()
            return
        else:
            print("Opção inválida. Digite 1, 2, 3 ou 0.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nEncerrado pelo usuário.")
