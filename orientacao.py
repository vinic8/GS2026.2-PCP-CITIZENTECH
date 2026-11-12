"""Uma orientação da base de conhecimento: um registro do JSON virado objeto."""


class Orientacao:
    """Guarda os dados de uma orientação e sabe se exibir na tela."""

    # Usado pela BaseConhecimento para validar cada registro do JSON.
    CAMPOS = (
        "id",
        "categoria",
        "titulo",
        "palavras_chave",
        "resposta",
        "documentos",
        "onde",
        "fonte",
        "verificado_em",
    )

    AVISO = "Aviso: este assistente NÃO é um canal oficial."

    def __init__(self, id, categoria, titulo, palavras_chave, resposta,
                 documentos, onde, fonte, verificado_em):
        self.id = id
        self.categoria = categoria
        self.titulo = titulo
        self.palavras_chave = palavras_chave
        self.resposta = resposta
        self.documentos = documentos
        self.onde = onde
        self.fonte = fonte
        self.verificado_em = verificado_em

    def exibir(self):
        """Imprime a orientação completa, sempre com fonte, data e aviso."""
        print(f"\n>> {self.titulo} [{self.categoria}]")
        print(self.resposta)
        print("\nDocumentos necessários:")
        for documento in self.documentos:
            print(f"  - {documento}")
        print(f"\nOnde: {self.onde}")
        print(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        print(self.AVISO)

    def __repr__(self):
        return f"Orientacao(id={self.id}, titulo={self.titulo!r})"
