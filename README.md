# Citizen Assist AI

Assistente de terminal, em Python puro, que orienta **jovens de 16 a 24 anos entrando no primeiro emprego** sobre documentos, trabalho e acesso a educação e renda. Responde apenas com informação verificada em fontes oficiais, mostra a fonte e a data de verificação em toda resposta, e nunca pede dados pessoais.

Global Solution 2026.2 — Pensamento Computacional e Automação com Python (desafio CitizenTech).

---

## Integrantes

| Nome | RM |
|---|---|
| Vinicius Molena | 571270 |
| Ricardo Algazi | 569600 |

---

## Público e problema

**Público:** jovens de 16 a 24 anos entrando no mercado de trabalho formal.

**Problema:** o primeiro emprego exige uma sequência de documentos e cadastros que ninguém ensina na escola, e a informação está espalhada por dezenas de portais com linguagem administrativa. O jovem não sabe a ordem (o CPF vem antes da identidade e da carteira de trabalho), não sabe o que é obrigatório (bolsa de estágio só é obrigatória no estágio não obrigatório), e cai em páginas que parecem oficiais e não são. Erros aqui custam caro: perder o prazo do alistamento impede concurso público e passaporte; não saber que a isenção do Enem não inscreve na prova custa um ano.

**Escopo da base:** 17 orientações em 3 categorias.

| Categoria | Orientações |
|---|---|
| Documentos | CPF, RG/CIN, título de eleitor, alistamento militar |
| Trabalho | Carteira de Trabalho Digital, PIS/NIS, Jovem Aprendiz, conseguir estágio, direitos do estágio, efetivação depois do estágio, procurar vaga pelo Sine, carteira não assinada, seguro-desemprego, regras para menores de 18 |
| Educação e Renda | Enem e isenção da taxa, Prouni e Fies, CadÚnico |

---

## ODS relacionados

- **ODS 8 — Trabalho decente e crescimento econômico.** O assistente explica direitos do contrato de aprendizagem e do estágio, e mostra como denunciar trabalho sem registro.
- **ODS 4 — Educação de qualidade.** Orienta sobre Enem, isenção da taxa, Prouni e Fies, e sobre a regra de que o trabalho não pode impedir a frequência escolar.
- **ODS 10 — Redução das desigualdades.** O público-alvo é justamente quem não tem alguém em casa que já passou por esse caminho. O CadÚnico, que destrava boa parte dos programas, é uma das orientações.
- **ODS 16 — Instituições eficazes.** Toda resposta carrega a fonte oficial e a data de verificação, e o assistente declara que não é canal oficial.

---

## Como executar

Requer apenas **Python 3.8 ou superior**. Nenhuma biblioteca externa.

```bash
python main.py
```

Para rodar a auto-verificação da busca e da base:

```bash
python teste_busca.py
```

### Estrutura

```
citizen-assist-ai/
├── README.md
├── main.py                  menu principal e laço do programa
├── orientacao.py            class Orientacao
├── base_conhecimento.py     normalizar() + class BaseConhecimento
├── assistente.py            class Assistente
├── teste_busca.py           auto-verificação com asserts
├── docs/                    spec de design do projeto
└── data/
    ├── base_conhecimento.json
    ├── historico.json
    └── atendimentos.csv
```

`teste_busca.py` é um arquivo que existe porque a normalização e pontuação são a única lógica do projeto que quebra em silêncio: ao editar o JSON, uma palavra-chave mal escrita não dá erro, só faz uma orientação deixar de ser encontrada. O teste pega isso. Ele confere, entre outras coisas, que **toda orientação é encontrada por cada uma das suas próprias palavras-chave**, que 17 perguntas escritas em linguagem natural chegam à orientação certa, e que JSON corrompido, registro incompleto e histórico ilegível não derrubam o programa.

### Organização em classes

Composição

```
Assistente
└── base: BaseConhecimento
    └── orientacoes: [Orientacao, Orientacao, ...]
```

| Classe | Responsabilidade | Métodos |
|---|---|---|
| `Orientacao` | Guardar um registro do JSON e exibi-lo | `exibir()` |
| `BaseConhecimento` | Ler o JSON, listar categorias e buscar | `carregar()`, `categorias()`, `por_categoria()`, `pontuar()`, `buscar()`, `confianca()` |
| `Assistente` | Atender, guardar histórico e calcular indicadores | `perguntar()`, `navegar()`, `registrar()`, `indicadores()`, `exportar_csv()`, `encerrar()` |

---

## Regra de pontuação

A pergunta, as palavras-chave e os títulos passam por `normalizar()`, que põe tudo em minúsculas, remove acentos por tabela, troca pontuação por espaço e **cerca o texto com espaços**. O cercamento é o que faz `" sus "` casar com a palavra inteira e não com o miolo de `"susto"`.

| Regra | Pontos |
|---|---|
| Palavra-chave da orientação que aparece na pergunta | **+3** |
| Palavra da pergunta com 4 ou mais letras que aparece no título | **+1** |

| Pontuação da melhor | Confiança |
|---|---|
| 6 ou mais | **ALTA** |
| 3 a 5 | **MÉDIA** |
| menos de 3 | não encontrou — sugere reformular e lista as categorias |

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)` ordenada da maior para a menor pontuação. O assistente mostra a melhor e até duas alternativas.

### Ajustes que fizemos

**Pesos e limiares são exatamente os do enunciado.** Mudamos duas coisas, ambas por motivo verificado em teste:

1. **`normalizar()` também remove `- / [ ] { } " '`**, além dos sinais do enunciado. Sem isso, `"e-título"` e `"e título"` viravam textos diferentes e a palavra-chave não casava.
2. **`buscar()` ordena com `key=lambda par: par[0]`**, não pelas tuplas diretas. Ordenar as tuplas estoura `TypeError` quando duas orientações empatam na pontuação, porque o Python passa a comparar os objetos `Orientacao`. Empate é comum numa base pequena. Há um teste cobrindo esse caso em `teste_busca.py`.

---

## Regras de atendimento

- **Dados pessoais:** a pergunta é recusada e **não é registrada** se contiver `@` ou 8 ou mais dígitos. Oito dígitos pega CPF (11), telefone (10 ou 11) e RG (9), e deixa passar `"tenho 16 anos"`, que é o comportamento desejado.
- **Entradas inválidas:** opção fora da faixa, letra onde se espera número, resposta vazia e `s/n` inválido apenas avisam e repetem a pergunta. **Nenhuma entrada encerra o programa**, em nenhuma tela. `0` volta em todas elas.
- **Transparência:** toda resposta mostra fonte, data de verificação e o aviso `este assistente NÃO é um canal oficial`.
- **Arquivos:** JSON ausente, JSON corrompido ou registro com campo faltando não derrubam o programa. Registro incompleto, ou com `palavras_chave`/`documentos` fora do tipo lista, é ignorado com aviso; os demais carregam normalmente. Um `historico.json` ilegível é renomeado para `.bak` antes de o programa começar um novo, para que a primeira gravação não apague os atendimentos que estavam nele.

---

## Histórico, indicadores e CSV

Cada pergunta digitada (ou orientação aberta pela navegação) gera um registro em `data/historico.json`, gravado **na hora** — um travamento no meio do teste com usuários não pode custar os atendimentos já feitos. O histórico **acumula entre sessões**, que é como se chega aos 10+ atendimentos de 3 pessoas exigidos.

Campos: `data`, `origem`, `pergunta`, `id_orientacao`, `encontrou`, `ajudou`, `tentativas`, `tempo_s`, `facilidade`.

`tentativas` é a posição da pergunta no ciclo: achou de primeira = 1, reformulou duas vezes = 3. O ciclo zera a cada resposta encontrada. O cronômetro também reinicia por ciclo, então o registro que encontrou carrega o tempo total até a solução.

Indicadores calculados: resposta encontrada (%), taxa de acerto (ajudou, sobre os atendimentos que encontraram), tempo médio para encontrar, tentativas por atendimento, facilidade de uso (1 a 5) e a lista de dúvidas sem solução.

Na saída, o assistente pede a nota de facilidade e exporta tudo para `data/atendimentos.csv` com `csv.DictWriter`.

---

## Fontes consultadas

Todas as orientações vêm de domínios oficiais (`gov.br`, `planalto.gov.br`, `tse.jus.br`, `poupatempo.sp.gov.br`), consultados em **12/11/2026**.

| # | Assunto | Fonte |
|---|---|---|
| 1 | CPF | https://www.gov.br/pt-br/servicos/inscrever-no-cpf |
| 2 | RG / CIN (SP) | https://www.poupatempo.sp.gov.br/carta/D97C3844-A2D9-4C9E-B364-CB4FEB26A1FB |
| 3 | Título de eleitor | https://www.tse.jus.br/servicos-eleitorais |
| 4 | Alistamento militar | https://www.gov.br/pt-br/servicos/alistar-se-no-servico-militar-obrigatorio |
| 5 | Carteira de Trabalho Digital | https://www.gov.br/pt-br/servicos/obter-a-carteira-de-trabalho |
| 6 | PIS / NIS / NIT | https://www.gov.br/inss/pt-br/direitos-e-deveres/inscricao-e-contribuicao/inscricao |
| 7 | Jovem Aprendiz | https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/aprendizagem-profissional |
| 8 | Estágio | https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11788.htm |
| 9 | Denúncia trabalhista | https://www.gov.br/pt-br/servicos/realizar-denuncia-trabalhista |
| 10 | Menor de 18 anos | https://www.planalto.gov.br/ccivil_03/leis/l8069.htm |
| 11 | Enem e isenção | https://www.gov.br/inep/pt-br/centrais-de-conteudo/noticias/enem/confira-o-passo-a-passo-para-pedir-isencao-da-taxa-de-inscricao |
| 12 | Prouni e Fies | https://www.gov.br/mec/pt-br/assuntos/noticias/2026/janeiro/publicado-edital-do-fies-para-o-1o-semestre-de-2026 |
| 13 | CadÚnico | https://www.gov.br/pt-br/servicos/inscrever-se-no-cadastro-unico-para-programas-sociais-do-governo-federal |
| 14 | Conseguir estágio | https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11788.htm |
| 15 | Efetivação depois do estágio | https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11788.htm |
| 16 | Vagas pelo Sine | https://www.gov.br/pt-br/servicos/buscar-emprego-no-sistema-nacional-de-emprego-sine |
| 17 | Seguro-desemprego | https://www.gov.br/pt-br/servicos/solicitar-o-seguro-desemprego |

Cada orientação carrega **uma** URL no campo `fonte`, que é a principal do assunto. Três delas apoiam-se também em páginas oficiais complementares, conferidas na mesma data:

| Orientação | Fonte de apoio | Para qual fato |
|---|---|---|
| 14 | https://www.gov.br/servidor/pt-br/acesso-a-informacao/gestao-de-pessoas/concursos-publicos-e-provimento-de-pessoal/programa-de-estagio | editais de estágio nos órgãos públicos |
| 15 | https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm | 5 dias úteis para anotar a admissão (art. 29), experiência de 90 dias (art. 445), exame admissional por conta da empresa (art. 168) |
| 15 | https://www.gov.br/trabalho-e-emprego/pt-br/servicos/trabalhador/carteira-de-trabalho/perguntas-frequentes-carteira-de-trabalho-digital | contrato visível em até 48 horas e correção pelo eSocial |
| 17 | https://www.gov.br/pt-br/temas/perguntas-frequentes-seguro-desemprego | prazo do 7º dia até 120 dias |

Uma decisão de conteúdo: **não existe um portal público nacional único de vagas de estágio**, só programas por órgão e portais estaduais. Por isso a orientação 14 manda procurar a própria instituição de ensino, que é quem atesta a matrícula e assina o termo.

Três informações que a pesquisa corrigiu e que circulam erradas:

- **Não há base federal para "14 anos para tirar a CTPS".** A página do serviço não cita idade, e o art. 415 da CLT, que criava a carteira para menores de 18, foi revogado pela Lei 13.874/2019. O que tem idade mínima é *trabalhar*: 16 anos, ou 14 como aprendiz.
- **O texto da CLT no Planalto ainda exibe redações da MP 1.116/2022, que caducou.** Quem lê desatento afirma contrato de aprendiz de 3 a 4 anos; o prazo em vigor é de 2 anos.
- **Bolsa e auxílio-transporte no estágio são obrigatórios apenas no estágio não obrigatório.** Dizer "a empresa é obrigada a pagar bolsa" sem a ressalva cria expectativa falsa.

---

## Bateria de validação (simulada)

**18 atendimentos em 3 sessões**, com entrada automatizada. Ela valida o fluxo inteiro e confere se cada pergunta cai na orientação certa. Os 18 atendimentos ficaram gravados em `data/historico.json` e `data/atendimentos.csv`, onde depois entram também os do teste com usuários: **esses arquivos guardam todo atendimento que aconteceu,**. A separação entre o que é simulado e o que é pessoa de verdade está aqui no README.

Para responder `s` ou `n` seguimos uma regra fixa: `s` quando a orientação devolvida de fato responde à pergunta, `n` quando ela é do assunto certo mas não resolve o que foi perguntado.

| Indicador | Resultado |
|---|---|
| Atendimentos registrados | 18 |
| Resposta encontrada | 88,9% |
| Taxa de acerto (ajudou) | 93,8% |
| Tempo médio para encontrar | 0,0 s — ver ressalva abaixo |
| Tentativas por atendimento | 1,2 |
| Facilidade de uso (1 a 5) | 4,3 |

**O tempo de 0,0 s é a prova de que esta bateria é simulada:** o cronômetro mede o intervalo real entre a pergunta e a resposta, e com entrada automatizada não existe intervalo. Tempo de verdade só aparece no teste com usuários.

**Dúvidas sem solução (2):**

- `preciso de ajuda com aluguel` — fora do escopo do assistente, que é o primeiro emprego.
- `como faço um currículo` — assunto real, mas não existe página de governo que ensine a escrever currículo. Preferimos o assistente dizer que não sabe a inventar conselho.

**Encontrou mas não resolveu (1):**

- `quanto ganha um estagiário` — caiu na orientação 8, que é a do assunto, mas a lei não fixa valor de bolsa; a resposta não traz o número que a pessoa queria.

**Perguntas que a bateria confirmou.** Quatro perguntas de uso comum e a orientação em que cada uma cai:

| Pergunta | Orientação |
|---|---|
| `como fazer um estágio?` | conseguir uma vaga de estágio (14) |
| `faço estágio e quero virar um júnior` | ser efetivado depois do estágio (15) |
| `como faço o seguro desemprego` | seguro-desemprego (17) |
| `como faço pra arrumar emprego` | procurar vaga nos canais do governo (16) |

### Como três orientações sobre estágio convivem na mesma busca

A base tem três orientações de estágio: **conseguir a vaga (14)**, **direitos de quem já estagia (8)** e **efetivação no fim (15)**. As três carregam a palavra-chave do assunto, `estagio`, então ela empata em todas e **quem decide é a frase de intenção**:

| Pergunta | Frase que decide | Pontuação |
|---|---|---|
| `como fazer um estágio?` | `fazer um estagio` → orientação 14 | 7 contra 4 |
| `faço estágio e quero virar um júnior` | `virar um junior` e `junior` → orientação 15 | 10 contra 4 |
| `tenho direito a bolsa no estágio` | nenhuma: empate em 4 pontos | fica com a 8, a primeira do arquivo |

---

## Teste com usuários

Três pessoas de fora da equipe usaram o assistente em **3 sessões separadas**, somando **15 atendimentos**. 
Nenhum nome ou dado de participante foi registrado: o histórico guarda só a pergunta, o resultado e o tempo.

Os arquivos `data/historico.json` e `data/atendimentos.csv` guardam todos os atendimentos juntos — os 18 da bateria simulada e os 15 deste teste —, porque registram tudo o que aconteceu. A primeira coluna abaixo é **só o teste com pessoas** (registros a partir de 14:18 de 12/11/2026); a segunda é o que a opção 3 do menu imprime, sobre os 33.

| Indicador | Teste com usuários (15) | Histórico completo (33) |
|---|---|---|
| Atendimentos registrados | 15 | 33 |
| Resposta encontrada (%) | 100,0% | 93,9% |
| Taxa de acerto (ajudou) | 80,0% | 87,1% |
| Tempo médio para encontrar | 11,3 s | 5,5 s |
| Tentativas por atendimento | 1,0 | 1,1 |
| Facilidade de uso (1 a 5) | 4,3 | 4,3 |

Oito atendimentos vieram da navegação por categorias e sete de pergunta em texto livre: os dois caminhos do menu foram usados.

**Dúvidas sem solução encontradas:** nenhuma. Toda pergunta encontrou uma orientação com 3 pontos ou mais.

**Encontrou, mas não resolveu (3)** — são estes os pontos fracos que o teste revelou:

| Pergunta | Foi para | Por que não ajudou |
|---|---|---|
| `como conseguir uma vaga de junior?` | Efetivação depois do estágio (15) | **Erro de palavra-chave.** `junior` levou para a efetivação; a pessoa queria vaga. Corrigido abaixo. |
| `meu rg esta vencido preciso trocar?` | RG / CIN (2) | **Lacuna de conteúdo.** A orientação ensina a tirar o documento, mas não fala de validade do RG antigo. |
| `como fazer o enem?` | Enem (11) | **Pergunta ampla.** A orientação trata de isenção e inscrição; a pessoa reformulou (`documentos pro enem quais são?`) e a segunda resposta ajudou. |

**Melhoria feita a partir do teste:**

Acrescentamos a palavra-chave `"vaga de junior"` à orientação 16 — Procurar vaga de emprego nos canais do governo.

| Pergunta | Antes | Depois |
|---|---|---|
| `como conseguir uma vaga de junior?` | Efetivação (15) com 3 pontos | **Procurar vaga (16) com 4 pontos**; a efetivação vira alternativa |

Conferimos o efeito colateral: `faço estágio e quero virar um júnior` continua na efetivação (10 pontos contra 4), e as 32 perguntas da bateria de rotas continuam caindo no lugar certo. O caso entrou em `teste_busca.py` para não voltar a quebrar.

Os dois outros pontos são de conteúdo, não de palavra-chave, e ficam como próximos passos: a validade do RG antigo e uma orientação geral sobre como funciona o Enem exigem nova pesquisa em fonte oficial antes de entrar na base.

---

## Limitações

1. **A nota de facilidade é por sessão**, replicada em todos os registros daquela sessão, porque o JSON é uma lista de atendimentos e a nota é pedida uma vez na saída. A média acaba ponderada pelo volume de atendimentos de cada sessão.
2. **A busca é por palavra-chave, sem sinônimos nem correção de digitação.** "carteirinha" não encontra "carteira". Ampliar a cobertura significa acrescentar palavras-chave ao JSON, não mudar o código.
3. **A base cobre 17 assuntos.** Fora deles o assistente diz que não sabe — por desenho, não inventa. Faltam de propósito assuntos sem fonte oficial, como "como faço um currículo": não existe página de governo que ensine isso, e inventar o conteúdo quebraria a regra do projeto.
4. **Orientações de alcance estadual usam São Paulo como referência** (RG/CIN e CadÚnico). Em outros estados o procedimento muda.
5. **O conteúdo envelhece.** Foi verificado em 12/11/2026. A pesquisa encontrou três casos de informação oficial que mudou ou caducou só em 2026 — entre eles o cadastro eleitoral, que ficou fechado de maio a 2 de novembro de 2026.
6. **Empate na pontuação é decidido pela ordem do arquivo.** Quando duas orientações fazem os mesmos pontos, vence a que vem primeiro no JSON. É o que mantém `tenho direito a bolsa no estágio` na orientação 8 em vez da 14. A perdedora ainda aparece em "Talvez também sirva".
7. **O assistente não é canal oficial** e não substitui o atendimento dos órgãos públicos. Ele mostra a fonte justamente para que a pessoa confirme antes de agir.

---

## Vídeo técnico

> **A PREENCHER** — link do YouTube (não listado).
