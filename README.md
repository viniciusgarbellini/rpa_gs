# 🛰️ Estacao de Controle de Missao

**Global Solution 2026 — AI for RPA (FIAP)**
Robo de automacao (RPA) que processa **telemetria espacial** de ponta a ponta:
gera os dados brutos de uma missao, estrutura com pandas, **detecta anomalias**,
carrega num banco SQLite, gera relatorios automaticos e disponibiliza tudo numa
**API REST** consumida por um **dashboard** web.

---

## 🎯 O problema

Uma missao espacial gera um volume enorme de dados nao estruturados (telemetria
de sensores e logs de bordo). Este robo automatiza o caminho **dado bruto →
inteligencia acionavel**, sem intervencao humana.

## 🔁 Fluxo do robo (ponta a ponta)

```
[1] Gera dados brutos      → telemetria.csv + logs_bordo.txt   (gerador_dados.py)
        ↓
[2] Le e estrutura (pandas)→ DataFrames limpos e validados      (processador.py)
        ↓
[3] Analise inteligente    → anomalias (z-score + limites) +    (analise.py)
                             classificacao NLP de logs + indice de saude
        ↓
[4] Carga no banco (SQLite)→ tabelas: telemetria, anomalias, logs (banco.py)
        ↓
[5] Artefatos automaticos  → relatorio_missao.xlsx + .md         (relatorio.py)
        ↓
[6] API REST (FastAPI)     → serve os dados estruturados         (api.py + model.py)
        ↓
[7] Front-end (dashboard)  → consome a API via Fetch             (frontend/index.html)
        ↓
[8] Agendamento (schedule) → roda o robo periodicamente          (agendador.py)
```

Tudo com **logging** e **tratamento de excecoes (try/except)** em cada etapa.

---

## 🚀 Como executar

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Rodar o robo (pipeline completo)
Gera os dados, analisa, carrega no banco e produz os artefatos:
```bash
python robo.py
```
Saidas geradas:
- `dados/telemetria.csv` e `dados/logs_bordo.txt` — dados brutos
- `missao.db` — banco SQLite com os dados estruturados
- `saida/relatorio_missao.xlsx` — planilha com 5 abas
- `saida/relatorio_missao.md` — relatorio consolidado
- `logs/estacao.log` — log da execucao

### 3. Subir a API + dashboard
```bash
python api.py
```
Depois acesse:
- **http://localhost:8000/** → dashboard (front-end)
- **http://localhost:8000/docs** → documentacao automatica da API

### 4. (Opcional) Rodar agendado
```bash
python agendador.py
```

### (Opcional) Com Docker
```bash
docker compose up --build
# acesse http://localhost:8000
```

---

## 🧩 Tecnologias e topicos do semestre integrados

| Topico da disciplina | Onde aparece |
|----------------------|--------------|
| Manipulacao de arquivos (CSV/TXT) | `gerador_dados.py`, `processador.py` |
| Analise de dados com **pandas** | `processador.py`, `analise.py` |
| Algoritmos de analise (anomalias) | `analise.py` |
| **NLP** (classificacao de logs por tema) | `analise.py` |
| Banco de dados com **sqlite3** | `banco.py`, `model.py` |
| **API REST** (FastAPI + Pydantic, MVC) | `api.py`, `model.py` |
| Front-end web (HTML/CSS/JS + Fetch) | `frontend/index.html` |
| Agendamento (**schedule**) | `agendador.py` |
| Containers (**Docker**) | `Dockerfile`, `docker-compose.yml` |

> O projeto integra **6+ topicos** do semestre — bem acima do minimo de 2 exigido.

---

## 📊 Como o projeto atende a matriz de avaliacao

| Criterio (peso) | Como e' atendido |
|-----------------|------------------|
| **Dominio Tecnico e Integracao (40%)** | Pipeline RPA funcional que integra 6+ topicos do semestre num fluxo unico de ponta a ponta. |
| **Arquitetura de Fluxo e Eng. de Software (25%)** | Codigo modular (1 modulo por etapa), orquestrador central, `try/except` e `logging` em todas as etapas, codigos de saida para automacao. |
| **Inteligencia de Dados e IA (20%)** | Algoritmos de analise: deteccao de anomalias por **z-score** (estatistico) + **limites de engenharia**, **NLP** (classificacao das mensagens de log por tema), classificacao por severidade e **indice de saude** da missao (calculo unificado entre robo e API). |
| **Entrega de Artefatos e Outputs (15%)** | Planilha Excel com 5 abas, relatorio Markdown consolidado, banco SQLite estruturado e **carga de dados para o front-end** via API. |

---

## 📁 Estrutura do projeto

```
estacao_controle_missao/
├── config.py            # configuracao central (caminhos, limites, parametros)
├── gerador_dados.py     # [1] gera os dados brutos da missao
├── processador.py       # [2] le e estrutura com pandas
├── analise.py           # [3] deteccao de anomalias + classificacao
├── banco.py             # [4] carga no banco SQLite
├── relatorio.py         # [5] gera Excel + relatorio Markdown
├── model.py             # camada Model da API (Repository + Pydantic)
├── api.py               # [6] API REST (FastAPI)
├── frontend/index.html  # [7] dashboard web
├── robo.py              # orquestrador do pipeline
├── agendador.py         # [8] agendamento com schedule
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

> Cada modulo pode ser executado isoladamente (`python analise.py`, etc.) para
> teste, ou em conjunto pelo orquestrador `robo.py`.
