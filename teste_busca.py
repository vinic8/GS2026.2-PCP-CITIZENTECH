"""Auto-verificação da busca e da base de conhecimento.

Rode com: python teste_busca.py

Cobre a normalização, a pontuação, o empate que quebraria a ordenação, o bloqueio
de dados pessoais e a integridade do JSON. Não substitui o teste com usuários:
serve para pegar o erro que não aparece na tela quando alguém edita o JSON.
"""

import json
import os
import tempfile

from assistente import Assistente
from base_conhecimento import BaseConhecimento, normalizar
from orientacao import Orientacao

RAIZ = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE = os.path.join(RAIZ, "data", "base_conhecimento.json")


def orientacao_de_teste(**mudancas):
    dados = dict(
        id=99,
        categoria="Teste",
        titulo="Fazer o Cartão Nacional de Saúde (Cartão SUS)",
        palavras_chave=["cartao sus", "cartao do sus", "sus"],
        resposta="Pode ser feito em uma UBS.",
        documentos=["Documento com foto"],
        onde="Qualquer UBS",
        fonte="https://www.gov.br/saude",
        verificado_em="2026-11-05",
    )
    dados.update(mudancas)
    return Orientacao(**dados)


def testar_normalizar():
    assert normalizar("Como faço o Cartão?") == " como faco o cartao "
    assert normalizar("  ÁÉÍÓÚ  ") == " aeiou "
    assert normalizar("a,b;c") == " a b c "
    assert normalizar("") == "  "
    # O cercamento com espaços evita casar uma palavra dentro de outra.
    assert " sus " not in normalizar("susto")
    assert " sus " in normalizar("cartão do SUS")


def testar_pontuacao():
    """O exemplo do enunciado: 'Como faço o cartão do SUS?' vale 7 pontos."""
    base = BaseConhecimento("(em memória)")
    pontos = base.pontuar(normalizar("Como faço o cartão do SUS?"), orientacao_de_teste())
    assert pontos == 7, f"esperava 7 pontos, veio {pontos}"
    assert base.confianca(pontos) == "ALTA"
    assert base.confianca(4) == "MÉDIA"
    assert base.confianca(2) is None


def testar_palavra_curta_nao_pontua_pelo_titulo():
    base = BaseConhecimento("(em memória)")
    # 'sus' tem 3 letras: não pontua pelo título, só pela palavra-chave.
    orientacao = orientacao_de_teste(palavras_chave=["inexistente"])
    assert base.pontuar(normalizar("sus"), orientacao) == 0


def testar_empate_nao_quebra_a_ordenacao():
    """Ordenar as tuplas direto estouraria TypeError ao comparar Orientacao."""
    base = BaseConhecimento("(em memória)")
    base.orientacoes = [
        orientacao_de_teste(id=1, titulo="Primeiro", palavras_chave=["igual"]),
        orientacao_de_teste(id=2, titulo="Segundo", palavras_chave=["igual"]),
    ]
    resultados = base.buscar("igual")
    assert [pontos for pontos, _ in resultados] == [3, 3]


def testar_busca_sem_resultado():
    base = BaseConhecimento("(em memória)")
    base.orientacoes = [orientacao_de_teste()]
    assert base.buscar("xyzw qwerty") == []


def testar_bloqueio_de_dado_pessoal():
    assert Assistente.tem_dado_pessoal("meu cpf é 123.456.789-00")
    assert Assistente.tem_dado_pessoal("me manda em fulano@email.com")
    assert Assistente.tem_dado_pessoal("meu telefone é 11 98765-4321")
    assert not Assistente.tem_dado_pessoal("como tirar a carteira de trabalho")
    assert not Assistente.tem_dado_pessoal("tenho 16 anos, posso trabalhar?")


def testar_integridade_da_base():
    base = BaseConhecimento(CAMINHO_BASE)
    assert base.carregar(), "a base de conhecimento não carregou"
    assert len(base.orientacoes) >= 10, "o enunciado pede no mínimo 10 orientações"
    assert len(base.categorias()) >= 3, "o enunciado pede no mínimo 3 categorias"

    ids = [o.id for o in base.orientacoes]
    assert len(ids) == len(set(ids)), "há ids repetidos na base"

    for o in base.orientacoes:
        assert len(o.palavras_chave) >= 3, f"orientação {o.id}: menos de 3 palavras-chave"
        assert o.documentos, f"orientação {o.id}: sem documentos"
        assert o.resposta.strip(), f"orientação {o.id}: resposta vazia"
        assert o.onde.strip(), f"orientação {o.id}: campo 'onde' vazio"
        assert o.fonte.startswith("https://"), f"orientação {o.id}: fonte não é https"
        assert len(o.verificado_em) == 10, f"orientação {o.id}: data fora do formato"


def _base_temporaria(conteudo):
    """Grava um arquivo .json temporário e devolve o caminho. Quem chama apaga."""
    descritor, caminho = tempfile.mkstemp(suffix=".json")
    with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
        if isinstance(conteudo, str):
            arquivo.write(conteudo)
        else:
            json.dump(conteudo, arquivo, ensure_ascii=False)
    return caminho


def testar_registro_ruim_nao_derruba_a_base():
    """Registro com campo faltando ou no tipo errado é ignorado; o resto carrega."""
    bom = dict(id=1, categoria="Teste", titulo="Um título",
               palavras_chave=["a", "b", "c"], resposta="texto", documentos=["RG"],
               onde="em algum lugar", fonte="https://www.gov.br",
               verificado_em="2026-11-12")
    sem_campo = {campo: valor for campo, valor in bom.items() if campo != "onde"}
    sem_campo["id"] = 2
    # String no lugar da lista: pontuaria letra por letra em vez de avisar.
    tipo_errado = dict(bom, id=3, palavras_chave="estagio")

    caminho = _base_temporaria([bom, sem_campo, tipo_errado])
    try:
        base = BaseConhecimento(caminho)
        assert base.carregar(), "um registro ruim não pode impedir a base de carregar"
        assert [o.id for o in base.orientacoes] == [1], "só o registro bom deveria entrar"
    finally:
        os.remove(caminho)


def testar_json_corrompido_nao_trava():
    """Arquivo que não é JSON: carregar() devolve False em vez de estourar."""
    caminho = _base_temporaria("{ isso aqui nao e json")
    try:
        assert BaseConhecimento(caminho).carregar() is False
    finally:
        os.remove(caminho)
    assert BaseConhecimento("data/arquivo_que_nao_existe.json").carregar() is False


def testar_historico_ilegivel_vira_copia():
    """Histórico corrompido é renomeado para .bak, não sobrescrito e perdido."""
    caminho = _base_temporaria("{ isso aqui nao e json")
    try:
        assistente = Assistente("teste", BaseConhecimento("(em memória)"),
                                caminho_historico=caminho, caminho_csv=caminho + ".csv")
        assert assistente.historico == []
        assert os.path.exists(caminho + ".bak"), "o histórico ruim deveria virar .bak"
    finally:
        for arquivo in (caminho, caminho + ".bak", caminho + ".csv"):
            if os.path.exists(arquivo):
                os.remove(arquivo)


def testar_toda_orientacao_e_encontravel():
    """Cada orientação precisa ser achada pelas suas próprias palavras-chave."""
    base = BaseConhecimento(CAMINHO_BASE)
    assert base.carregar()
    for orientacao in base.orientacoes:
        for palavra_chave in orientacao.palavras_chave:
            resultados = base.buscar(palavra_chave)
            achados = [o.id for _, o in resultados]
            assert orientacao.id in achados, (
                f"a orientação {orientacao.id} não é encontrada pela própria "
                f"palavra-chave {palavra_chave!r}")


def testar_perguntas_reais():
    """Perguntas escritas como um jovem escreveria, com a orientação esperada."""
    base = BaseConhecimento(CAMINHO_BASE)
    assert base.carregar()

    casos = [
        ("como faço minha carteira de trabalho?", 5),
        ("quero tirar o CPF", 1),
        ("o que é jovem aprendiz", 7),
        ("tenho direito a bolsa no estágio?", 8),
        ("meu patrão não assinou minha carteira", 9),
        ("como pedir isenção da taxa do enem", 11),
        ("quero bolsa pelo prouni", 12),
        ("o que é o cadastro unico", 13),
        ("preciso me alistar no serviço militar", 4),
        ("como tirar título de eleitor", 3),
        # As três orientações de estágio dividem a palavra-chave do assunto:
        # o que decide entre elas é a frase de intenção da pergunta.
        ("como fazer um estágio?", 14),
        ("quero estagiar, por onde começo", 14),
        ("faço estágio e quero virar um júnior", 15),
        ("vou ser efetivado, o que muda?", 15),
        ("onde procurar vaga de emprego", 16),
        # Veio do teste com usuários: ia para a efetivação (15) por causa de "junior".
        ("como conseguir uma vaga de junior?", 16),
        ("como faço o seguro desemprego", 17),
    ]

    for pergunta, id_esperado in casos:
        resultados = base.buscar(pergunta)
        assert resultados, f"{pergunta!r} não encontrou nada"
        pontos, melhor = resultados[0]
        assert pontos >= base.MINIMO_PARA_RESPONDER, (
            f"{pergunta!r} ficou com {pontos} pontos, abaixo do mínimo para responder")
        assert melhor.id == id_esperado, (
            f"{pergunta!r} deveria achar a orientação {id_esperado}, "
            f"mas achou a {melhor.id} ({melhor.titulo!r})")


if __name__ == "__main__":
    testar_normalizar()
    testar_pontuacao()
    testar_palavra_curta_nao_pontua_pelo_titulo()
    testar_empate_nao_quebra_a_ordenacao()
    testar_busca_sem_resultado()
    testar_bloqueio_de_dado_pessoal()
    testar_integridade_da_base()
    print("(os AVISO e ERRO abaixo são esperados: são os testes de arquivo ruim)")
    testar_registro_ruim_nao_derruba_a_base()
    testar_json_corrompido_nao_trava()
    testar_historico_ilegivel_vira_copia()
    testar_toda_orientacao_e_encontravel()
    testar_perguntas_reais()
    print("OK - todos os testes passaram.")
