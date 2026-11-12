"""A base de conhecimento: lê o JSON, lista categorias e busca por pontuação."""

import json

from orientacao import Orientacao

ACENTOS = {
    "á": "a", "à": "a", "ã": "a", "â": "a",
    "é": "e", "ê": "e",
    "í": "i",
    "ó": "o", "õ": "o", "ô": "o",
    "ú": "u",
    "ç": "c",
}


def normalizar(texto):
    """Põe o texto em minúsculas, sem acento e sem pontuação, cercado por espaços.

    O cercamento com espaços é o truque que faz ' sus ' casar com a palavra
    inteira e não com o miolo de 'susto'.
    """
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in "?!.,;:()[]{}\"'/-":
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    """O conjunto de todas as orientações."""

    PONTOS_PALAVRA_CHAVE = 3
    PONTOS_TITULO = 1
    TAMANHO_MINIMO_DA_PALAVRA = 4
    MINIMO_PARA_RESPONDER = 3
    MINIMO_CONFIANCA_ALTA = 6

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao. Devolve True se deu certo.

        Arquivo ausente, JSON corrompido ou registro incompleto não derrubam o
        programa: avisam e seguem com o que der para aproveitar.
        """
        try:
            with open(self.caminho, encoding="utf-8") as arquivo:
                registros = json.load(arquivo)
        except FileNotFoundError:
            print(f"ERRO: não encontrei o arquivo {self.caminho}.")
            return False
        except json.JSONDecodeError as erro:
            print(f"ERRO: o arquivo {self.caminho} está corrompido ({erro}).")
            return False
        except OSError as erro:
            print(f"ERRO ao ler {self.caminho}: {erro}")
            return False

        if not isinstance(registros, list):
            print(f"ERRO: {self.caminho} deveria conter uma lista de orientações.")
            return False

        self.orientacoes = []
        for posicao, registro in enumerate(registros, start=1):
            if not isinstance(registro, dict):
                print(f"AVISO: registro {posicao} ignorado, não é um objeto JSON.")
                continue
            faltando = [campo for campo in Orientacao.CAMPOS if campo not in registro]
            if faltando:
                print(f"AVISO: registro {posicao} ignorado, faltam os campos: "
                      f"{', '.join(faltando)}")
                continue
            # palavras_chave e documentos são percorridos campo a campo: uma string
            # no lugar da lista não quebraria nada na hora, só pontuaria letra por
            # letra e imprimiria uma letra por documento.
            fora_do_tipo = [campo for campo in ("palavras_chave", "documentos")
                            if not isinstance(registro[campo], list)]
            if fora_do_tipo:
                print(f"AVISO: registro {posicao} ignorado, estes campos deveriam "
                      f"ser listas: {', '.join(fora_do_tipo)}")
                continue

            dados = {campo: registro[campo] for campo in Orientacao.CAMPOS}
            self.orientacoes.append(Orientacao(**dados))

        if not self.orientacoes:
            print("ERRO: nenhuma orientação válida foi encontrada na base.")
            return False
        return True

    def categorias(self):
        """Categorias únicas, em ordem alfabética."""
        return sorted({orientacao.categoria for orientacao in self.orientacoes})

    def por_categoria(self, categoria):
        return [o for o in self.orientacoes if o.categoria == categoria]

    def pontuar(self, pergunta_norm, orientacao):
        """+3 por palavra-chave que aparece na pergunta, +1 por palavra no título."""
        pontos = 0

        for palavra_chave in orientacao.palavras_chave:
            if normalizar(palavra_chave) in pergunta_norm:
                pontos += self.PONTOS_PALAVRA_CHAVE

        titulo_norm = normalizar(orientacao.titulo)
        for palavra in set(pergunta_norm.split()):
            if len(palavra) >= self.TAMANHO_MINIMO_DA_PALAVRA and f" {palavra} " in titulo_norm:
                pontos += self.PONTOS_TITULO

        return pontos

    def buscar(self, pergunta):
        """Devolve [(pontos, orientacao), ...] da maior para a menor pontuação."""
        pergunta_norm = normalizar(pergunta)
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta_norm, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))

        # Ordenar as tuplas direto estoura TypeError no empate, porque o Python
        # passa a comparar os objetos Orientacao. Empate é comum numa base pequena.
        resultados.sort(key=lambda par: par[0], reverse=True)
        return resultados

    def confianca(self, pontos):
        """'ALTA', 'MÉDIA' ou None quando a pontuação é baixa demais para responder."""
        if pontos >= self.MINIMO_CONFIANCA_ALTA:
            return "ALTA"
        if pontos >= self.MINIMO_PARA_RESPONDER:
            return "MÉDIA"
        return None
