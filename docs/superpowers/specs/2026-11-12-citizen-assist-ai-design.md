# Citizen Assist AI — spec de design

**Data:** 2026-11-12
**Equipe:** Vinicius Molena (RM 571270), Ricardo Algazi (RM 569600)
**Disciplina:** Pensamento Computacional e Automação com Python — GS 2026.2

---

## 1. O que é

Assistente de terminal, em Python puro, que responde dúvidas de **jovens de 16 a 24 anos entrando no primeiro emprego**, usando apenas uma base de conhecimento verificada em fontes oficiais. Mostra fonte e data de verificação em toda resposta, não coleta dado pessoal, e registra os atendimentos para calcular indicadores.

**Critério de sucesso:** roda com `python main.py` sem erro, cobre os 8 critérios da rubrica, e dá material claro para explicar no vídeo.

**Fora de escopo:** interface gráfica, dependências externas, integração com outras disciplinas, qualquer chamada de rede em tempo de execução.

---

## 2. Base de conhecimento

13 orientações em 3 categorias, extraídas do relatório de pesquisa em
`reports/Orientações para jovens no primeiro emprego.md`.

| Categoria | Orientações |
|---|---|
| Documentos | CPF, RG/CIN (referência SP), título de eleitor, alistamento militar |
| Trabalho | CTPS Digital, PIS/NIS, Jovem Aprendiz, estágio, carteira não assinada, menor de 18 anos |
| Educação e Renda | Enem + isenção, Prouni/Fies, CadÚnico |

Supera o mínimo do enunciado (10 orientações, 3 categorias, 3 palavras-chave).

**Pendência conhecida:** a `fonte` da orientação do título de eleitor (`tse.jus.br`) não pôde ser aberta na pesquisa — todo o domínio `jus.br` responde 403 a acesso automatizado. Precisa ser confirmada num navegador antes da entrega. A orientação do PIS/NIS usa como `fonte` a página do INSS no gov.br, que foi aberta e confirmada; a Caixa aparece apenas no campo `onde`.

---

## 3. Estrutura de arquivos

```
citizen-assist-ai/
├── README.md
├── main.py                  menu principal e laço do programa
├── orientacao.py            class Orientacao
├── base_conhecimento.py     normalizar() + class BaseConhecimento
├── assistente.py            class Assistente
├── teste_busca.py           auto-verificação com asserts
└── data/
    ├── base_conhecimento.json
    ├── historico.json
    └── atendimentos.csv
```

`teste_busca.py` é o único arquivo além dos quatro que o enunciado pede. Justificativa: normalização e pontuação valem 1,5 ponto e são a única lógica que quebra em silêncio quando o JSON muda. São ~30 linhas de `assert`, rodam com `python teste_busca.py`, e rendem a "decisão técnica" do roteiro do vídeo.

**Todo acesso a arquivo usa `encoding="utf-8"` explícito.** No Windows o `open()` usa a codificação da região por padrão, o que corromperia os acentos do JSON.

---

## 4. Classes

Composição: `Assistente` → `BaseConhecimento` → lista de `Orientacao`.

### `Orientacao` (orientacao.py)

| Atributo | Tipo |
|---|---|
| `id` | int |
| `categoria` | str |
| `titulo` | str |
| `palavras_chave` | list[str] |
| `resposta` | str |
| `documentos` | list[str] |
| `onde` | str |
| `fonte` | str |
| `verificado_em` | str (YYYY-MM-DD) |

**`exibir()`** — imprime título, categoria, resposta, lista de documentos, onde, fonte com data de verificação, e o aviso `este assistente NÃO é um canal oficial`. Não retorna nada.

### `BaseConhecimento` (base_conhecimento.py)

| Atributo | Tipo |
|---|---|
| `caminho` | str |
| `orientacoes` | list[Orientacao] |

**`carregar() -> bool`** — lê o JSON e cria os objetos `Orientacao`. Trata três falhas sem derrubar o programa:
- arquivo ausente (`FileNotFoundError`) → mensagem clara, retorna `False`
- JSON corrompido (`json.JSONDecodeError`) → mensagem clara, retorna `False`
- registro com campo obrigatório faltando → pula o registro, avisa qual `id`, continua

**`categorias() -> list[str]`** — categorias únicas, ordenadas.

**`por_categoria(categoria) -> list[Orientacao]`**

**`pontuar(pergunta_norm, orientacao) -> int`** — regra de pontuação da seção 5.

**`buscar(pergunta) -> list[tuple[int, Orientacao]]`** — pontua todas, descarta as de pontuação zero, ordena da maior para a menor.

### `Assistente` (assistente.py)

| Atributo | Tipo |
|---|---|
| `nome` | str |
| `base` | BaseConhecimento |
| `historico` | list[dict] |

**`perguntar()`** — laço de pergunta em texto livre (seção 6).
**`navegar()`** — navegação por categorias (seção 7).
**`registrar(...)`** — acrescenta um atendimento ao histórico e grava `data/historico.json`.
**`indicadores()`** — calcula e imprime os seis indicadores (seção 9).
**`exportar_csv()`** — grava `data/atendimentos.csv` com `csv.DictWriter`.

---

## 5. Normalização e pontuação

### `normalizar(texto) -> str`

Função de módulo em `base_conhecimento.py`. Minúsculas, remove acentos por tabela, troca pontuação por espaço, colapsa espaços, e devolve o texto **cercado por espaços** (` texto `). O cercamento é o que permite casar palavra inteira com `in`, sem achar "sus" dentro de "susto".

### Regra de pontuação

| Regra | Pontos |
|---|---|
| Palavra-chave da orientação que aparece na pergunta | +3 |
| Palavra da pergunta com 4+ letras que aparece no título | +1 |

Palavras repetidas na pergunta contam uma vez só (usa `set`).

| Pontuação da melhor | Confiança |
|---|---|
| 6 ou mais | ALTA |
| 3 a 5 | MÉDIA |
| menos de 3 | não encontrou |

Pesos e limites são os do enunciado, sem ajuste.

### Ordenação — cuidado

`buscar()` ordena com `key=lambda par: par[0]`. Ordenar as tuplas diretamente estoura `TypeError` quando duas orientações empatam, porque o Python tenta comparar os objetos `Orientacao`. Empate é comum numa base pequena.

---

## 6. Fluxo da pergunta em texto livre

```
Digite sua dúvida (0 para voltar):
```

1. `0` → volta ao menu.
2. Entrada vazia → avisa e repete. Não registra, não conta tentativa.
3. **Dado pessoal** → avisa `Atenção: não digite CPF, telefone ou e-mail. Reescreva.`, repete. **Não registra, não conta tentativa.** Detecção: a pergunta contém `@`, **ou** tem 8 ou mais dígitos no total.
4. Caso normal → `tentativas += 1`, busca.
   - **Melhor ≥ 3 pontos:** mostra confiança e pontuação, `exibir()` da melhor, até 2 alternativas (só título e categoria). Pergunta `Essa orientação respondeu sua dúvida? (s/n):` até receber `s` ou `n`. Registra com `encontrou=True`. Zera `tentativas` e reinicia o cronômetro.
   - **Nenhuma com 3 pontos:** mensagem de não encontrado, sugere reformular e lista as categorias. Registra com `encontrou=False`, `ajudou=False`, `id_orientacao=None`. **Mantém** o contador de tentativas.

O cronômetro (`time.time()`) reinicia a cada ciclo, não a cada pergunta. Assim o registro que encontrou carrega o tempo total até a solução, que é o que o indicador "tempo médio para encontrar" deve medir.

---

## 7. Navegação por categorias

Lista as categorias numeradas com `0 para voltar`. Escolhida uma, lista as orientações dela numeradas, também com `0 para voltar`. Escolhida uma orientação, chama `exibir()` e pergunta se resolveu.

Opção fora da faixa, letra ou entrada vazia → avisa e repete. **Nenhuma entrada inválida encerra o programa, em nenhuma tela.**

Registro: `origem="categoria"`, `pergunta` recebe o título escolhido, `tentativas=1`.

---

## 8. Histórico

Um registro por pergunta digitada (ou por orientação aberta via categoria), em `data/historico.json`:

```json
{
  "data": "2026-11-12T14:32:05",
  "origem": "pergunta",
  "pergunta": "como faco a carteira de trabalho",
  "id_orientacao": 5,
  "encontrou": true,
  "ajudou": true,
  "tentativas": 2,
  "tempo_s": 18.4,
  "facilidade": 4
}
```

**Decisões de modelagem, e por quê:**

1. **Um registro por pergunta.** A alternativa — um registro por ciclo inteiro — faria as perguntas sem resposta sumirem do histórico, e "lista de dúvidas sem solução" é um indicador obrigatório.
2. **`tentativas` é a posição da pergunta no ciclo.** Achou de primeira = 1; reformulou duas vezes = 3. O ciclo zera a cada resposta encontrada.
3. **`facilidade` é por sessão, gravada em todos os registros daquela sessão.** O JSON é uma lista de atendimentos e a nota é uma só, pedida na saída. Consequência assumida: a média pondera pelo número de atendimentos de cada sessão. Está declarada em Limitações.
4. **O histórico acumula entre sessões.** Carrega o arquivo existente ao abrir e dá append. Sem isso não se chega aos 10+ atendimentos de 3 pessoas que o teste com usuários exige.
5. **Grava a cada registro**, não só na saída. Um travamento no meio do teste com usuário não pode custar os atendimentos já feitos.

---

## 9. Indicadores

| Indicador | Cálculo |
|---|---|
| Resposta encontrada (%) | registros com `encontrou` ÷ total |
| Taxa de acerto: ajudou (%) | `ajudou` ÷ registros com `encontrou` |
| Tempo médio para encontrar | média de `tempo_s` nos registros com `encontrou` |
| Tentativas por atendimento | média de `tentativas` |
| Facilidade de uso (1 a 5) | média de `facilidade`, ignorando nulos |
| Dúvidas sem solução | perguntas dos registros com `encontrou=False` e `origem="pergunta"` |

Base vazia → imprime "ainda não há atendimentos registrados", sem divisão por zero.

---

## 10. Exportação CSV

`data/atendimentos.csv` via `csv.DictWriter`, com todas as colunas do registro, gravado na saída do programa.

Usa `encoding="utf-8-sig"` e `newline=""`. O BOM faz o Excel abrir os acentos corretamente; sem `newline=""` o `csv` escreve linha em branco entre registros no Windows.

---

## 11. Saída do programa

Pede a nota de facilidade de 1 a 5, validando a entrada em laço. Aplica a nota aos registros da sessão, grava o histórico, exporta o CSV e imprime os indicadores.

---

## 12. Teste automatizado

`teste_busca.py`, com `assert`, cobrindo:
- `normalizar()` remove acentos, pontuação e caixa, e cerca com espaços
- palavra-chave de várias palavras casa; palavra curta dentro de outra não casa
- a pontuação do exemplo do enunciado bate (cartão do SUS = 7 pontos) — adaptada à nossa base
- `buscar()` não estoura com empate de pontuação
- toda orientação do JSON tem os 9 campos, ao menos 3 palavras-chave e uma `fonte` que começa com `https://`
- a base tem ao menos 10 orientações e 3 categorias

Imprime `OK` e sai com código 0 quando tudo passa.

---

## 13. Limitações declaradas

1. A nota de facilidade é por sessão, replicada nos registros daquela sessão — a média pondera pelo volume de atendimentos de cada sessão.
2. A busca é por palavra-chave, sem sinônimos nem correção de digitação: "carteirinha" não acha "carteira".
3. A base cobre 13 assuntos. Fora deles o assistente diz que não sabe, por desenho — não inventa.
4. Orientações de alcance estadual (RG/CIN, CadÚnico) usam São Paulo como referência.
5. O conteúdo foi verificado em 2026-11-12 e envelhece. A pesquisa achou três casos de informação oficial que mudou ou caducou em 2026.
6. A `fonte` da orientação do título de eleitor não pôde ser aberta automaticamente e precisa de conferência humana.

---

## 14. Mapa para a rubrica

| Critério | Pts | Onde está |
|---|---|---|
| Funcionamento e modularização | 1,0 | 5 arquivos `.py`, menu completo (§3) |
| Base JSON | 1,0 | 13 orientações, 3 categorias, fontes oficiais (§2) |
| Orientação a Objetos | 2,0 | 3 classes por composição (§4) |
| Busca e navegação | 1,5 | §5, §6, §7 |
| Histórico, indicadores, CSV | 1,0 | §8, §9, §10 |
| Entradas inválidas, dados pessoais, avisos | 0,5 | §6.2, §6.3, §7, `exibir()` |
| GitHub, README, teste com usuários | 0,5 | README (fora desta spec) |
| Vídeo técnico | 2,5 | **Fora de escopo por decisão da equipe.** |

Os 7,5 pontos de código e documentação estão cobertos. O vídeo vale 2,5 e é responsabilidade da equipe; o enunciado avisa que funcionalidade não demonstrada no vídeo não pontua, então a spec marca em §12 e §13 os pontos que valem a pena mostrar.
