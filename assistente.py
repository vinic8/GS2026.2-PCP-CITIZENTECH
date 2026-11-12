"""O assistente: conversa com o cidadão, guarda o histórico e calcula indicadores."""

import csv
import json
import os
import time
from datetime import datetime


class Assistente:
    """Quem conversa com o cidadão."""

    CAMPOS_DO_ATENDIMENTO = (
        "data",
        "origem",
        "pergunta",
        "id_orientacao",
        "encontrou",
        "ajudou",
        "tentativas",
        "tempo_s",
        "facilidade",
    )

    MINIMO_DE_DIGITOS_SUSPEITO = 8

    def __init__(self, nome, base, caminho_historico="data/historico.json",
                 caminho_csv="data/atendimentos.csv"):
        self.nome = nome
        self.base = base
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        self.historico = []
        self.atendimentos_da_sessao = []
        self._carregar_historico()

    # ---------- dados pessoais ----------

    @classmethod
    def tem_dado_pessoal(cls, texto):
        """True se a pergunta parece conter e-mail, CPF, RG ou telefone.

        Oito dígitos ou mais pega CPF (11), telefone (10 ou 11) e RG (9). Datas e
        idades ('tenho 16 anos') passam, que é o comportamento desejado.
        """
        if "@" in texto:
            return True
        digitos = sum(1 for caractere in texto if caractere.isdigit())
        return digitos >= cls.MINIMO_DE_DIGITOS_SUSPEITO

    # ---------- atendimento por pergunta ----------

    def perguntar(self):
        """Laço de perguntas em texto livre. '0' volta ao menu."""
        inicio = time.time()
        tentativas = 0

        while True:
            pergunta = input("\nDigite sua dúvida (0 para voltar): ").strip()

            if pergunta == "0":
                return
            if not pergunta:
                print("Digite alguma coisa, ou 0 para voltar.")
                continue
            if self.tem_dado_pessoal(pergunta):
                print("Atenção: não digite CPF, telefone ou e-mail. Reescreva.")
                continue

            tentativas += 1
            resultados = self.base.buscar(pergunta)
            melhor = resultados[0] if resultados else None

            if melhor is None or melhor[0] < self.base.MINIMO_PARA_RESPONDER:
                self._mostrar_nao_encontrei()
                self.registrar(
                    origem="pergunta", pergunta=pergunta, id_orientacao=None,
                    encontrou=False, ajudou=False, tentativas=tentativas,
                    tempo_s=round(time.time() - inicio, 1),
                )
                continue

            pontos, orientacao = melhor
            print(f"\nConfiança da resposta: {self.base.confianca(pontos)} ({pontos} pontos)")
            orientacao.exibir()
            self._mostrar_alternativas(resultados[1:3])

            ajudou = self._perguntar_sim_ou_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
            self.registrar(
                origem="pergunta", pergunta=pergunta, id_orientacao=orientacao.id,
                encontrou=True, ajudou=ajudou, tentativas=tentativas,
                tempo_s=round(time.time() - inicio, 1),
            )

            # A dúvida foi atendida: começa um novo ciclo de tentativas e de tempo.
            tentativas = 0
            inicio = time.time()

    def _mostrar_nao_encontrei(self):
        print("\nNão encontrei uma orientação para essa dúvida.")
        print("Tente outras palavras, ou veja estas categorias:")
        for categoria in self.base.categorias():
            print(f"  - {categoria}")

    @staticmethod
    def _mostrar_alternativas(alternativas):
        if not alternativas:
            return
        print("\nTalvez também sirva:")
        for pontos, orientacao in alternativas:
            print(f"  - {orientacao.titulo} [{orientacao.categoria}] ({pontos} pontos)")

    # ---------- navegação por categorias ----------

    def navegar(self):
        """Menu de categorias. '0' volta em todas as telas."""
        while True:
            categorias = self.base.categorias()
            print("\n--- Categorias ---")
            for numero, categoria in enumerate(categorias, start=1):
                quantidade = len(self.base.por_categoria(categoria))
                print(f"  {numero}. {categoria} ({quantidade})")
            print("  0. Voltar")

            escolha = self._escolher_numero("Escolha uma categoria: ", len(categorias))
            if escolha == 0:
                return
            self._navegar_na_categoria(categorias[escolha - 1])

    def _navegar_na_categoria(self, categoria):
        orientacoes = self.base.por_categoria(categoria)
        inicio = time.time()

        while True:
            print(f"\n--- {categoria} ---")
            for numero, orientacao in enumerate(orientacoes, start=1):
                print(f"  {numero}. {orientacao.titulo}")
            print("  0. Voltar")

            escolha = self._escolher_numero("Escolha uma orientação: ", len(orientacoes))
            if escolha == 0:
                return

            orientacao = orientacoes[escolha - 1]
            orientacao.exibir()
            ajudou = self._perguntar_sim_ou_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
            self.registrar(
                origem="categoria", pergunta=orientacao.titulo,
                id_orientacao=orientacao.id, encontrou=True, ajudou=ajudou,
                tentativas=1, tempo_s=round(time.time() - inicio, 1),
            )
            inicio = time.time()

    # ---------- entradas do usuário ----------

    @staticmethod
    def _perguntar_sim_ou_nao(mensagem):
        while True:
            resposta = input(mensagem).strip().lower()
            if resposta in ("s", "sim"):
                return True
            if resposta in ("n", "nao", "não"):
                return False
            print("Responda apenas s (sim) ou n (não).")

    @staticmethod
    def _escolher_numero(mensagem, maximo, minimo=0):
        """Lê um número inteiro na faixa. Entrada inválida nunca encerra nada."""
        while True:
            escolha = input(mensagem).strip()
            if not escolha.isdigit():
                print(f"Digite um número de {minimo} a {maximo}.")
                continue
            numero = int(escolha)
            if minimo <= numero <= maximo:
                return numero
            print(f"Digite um número de {minimo} a {maximo}.")

    # ---------- histórico ----------

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou,
                  tentativas, tempo_s):
        """Guarda um atendimento e grava o histórico em disco na hora."""
        atendimento = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "origem": origem,
            "pergunta": pergunta,
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_s": tempo_s,
            "facilidade": None,
        }
        self.historico.append(atendimento)
        self.atendimentos_da_sessao.append(atendimento)
        # Grava a cada atendimento: um travamento no meio do teste com usuários
        # não pode custar os atendimentos já feitos.
        self._gravar_historico()

    def _carregar_historico(self):
        try:
            with open(self.caminho_historico, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            return
        except (json.JSONDecodeError, OSError) as erro:
            print(f"AVISO: não consegui ler o histórico ({erro}).")
            self._guardar_historico_ilegivel()
            return

        if isinstance(dados, list):
            self.historico = dados
        else:
            print("AVISO: o histórico não é uma lista.")
            self._guardar_historico_ilegivel()

    def _guardar_historico_ilegivel(self):
        """Renomeia o histórico que não deu para ler, em vez de deixar que a
        primeira gravação da sessão apague os atendimentos que estavam nele."""
        copia = self.caminho_historico + ".bak"
        try:
            os.replace(self.caminho_historico, copia)
            print(f"O arquivo anterior foi guardado em {copia}. Começando um novo.")
        except OSError as erro:
            print(f"AVISO: não consegui guardar uma cópia dele ({erro}). Começando um novo.")

    def _gravar_historico(self):
        try:
            pasta = os.path.dirname(self.caminho_historico)
            if pasta:
                os.makedirs(pasta, exist_ok=True)
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError as erro:
            print(f"AVISO: não consegui gravar o histórico ({erro}).")

    # ---------- indicadores e exportação ----------

    def indicadores(self):
        """Imprime os seis indicadores sobre todo o histórico acumulado."""
        print("\n=== Indicadores ===")
        total = len(self.historico)
        if total == 0:
            print("Ainda não há atendimentos registrados.")
            return

        encontrados = [a for a in self.historico if a["encontrou"]]
        ajudaram = [a for a in encontrados if a["ajudou"]]
        notas = [a["facilidade"] for a in self.historico if a["facilidade"] is not None]

        print(f"Atendimentos registrados: {total}")
        print(f"Resposta encontrada: {100 * len(encontrados) / total:.1f}%")

        if encontrados:
            print(f"Taxa de acerto (ajudou): {100 * len(ajudaram) / len(encontrados):.1f}%")
            tempo_medio = sum(a["tempo_s"] for a in encontrados) / len(encontrados)
            print(f"Tempo médio para encontrar: {tempo_medio:.1f} segundos")
        else:
            print("Taxa de acerto (ajudou): ainda sem dados")
            print("Tempo médio para encontrar: ainda sem dados")

        media_tentativas = sum(a["tentativas"] for a in self.historico) / total
        print(f"Tentativas por atendimento: {media_tentativas:.1f}")

        if notas:
            print(f"Facilidade de uso (1 a 5): {sum(notas) / len(notas):.1f}")
        else:
            print("Facilidade de uso (1 a 5): ainda sem dados")

        sem_solucao = [a["pergunta"] for a in self.historico
                       if not a["encontrou"] and a["origem"] == "pergunta"]
        print(f"\nDúvidas sem solução ({len(sem_solucao)}):")
        if sem_solucao:
            for pergunta in sem_solucao:
                print(f"  - {pergunta}")
        else:
            print("  (nenhuma)")

    def exportar_csv(self):
        """Grava todo o histórico em CSV. Devolve True se conseguiu."""
        if not self.historico:
            print("Nada para exportar: o histórico está vazio.")
            return False
        try:
            pasta = os.path.dirname(self.caminho_csv)
            if pasta:
                os.makedirs(pasta, exist_ok=True)
            # utf-8-sig para o Excel abrir os acentos certos;
            # newline="" para o csv não pular linha entre registros no Windows.
            with open(self.caminho_csv, "w", encoding="utf-8-sig", newline="") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=list(self.CAMPOS_DO_ATENDIMENTO))
                escritor.writeheader()
                escritor.writerows(self.historico)
        except OSError as erro:
            print(f"ERRO ao exportar o CSV: {erro}")
            return False
        print(f"Atendimentos exportados para {self.caminho_csv}")
        return True

    # ---------- saída ----------

    def encerrar(self):
        """Pede a nota de facilidade, salva tudo e mostra os indicadores."""
        if self.atendimentos_da_sessao:
            nota = self._escolher_numero(
                "\nDe 1 a 5, quão fácil foi usar o assistente? ", maximo=5, minimo=1)
            for atendimento in self.atendimentos_da_sessao:
                atendimento["facilidade"] = nota
            self._gravar_historico()

        self.indicadores()
        self.exportar_csv()
        print(f"\nObrigado por usar o {self.nome}.")
