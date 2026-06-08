"""
config.py
-----------------------------------------------------------------------------
Configuracao central da Estacao de Controle de Missao.

Concentra os caminhos de arquivos, os parametros da missao e os limites
operacionais usados na deteccao de anomalias. Manter tudo aqui evita
"numeros magicos" espalhados pelo codigo e facilita a manutencao do robo.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Diretorios do projeto (criados automaticamente quando o robo executa)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"      # entrada: arquivos brutos da missao
SAIDA_DIR = BASE_DIR / "saida"      # saida: artefatos gerados pelo robo
LOG_DIR = BASE_DIR / "logs"         # logs de execucao do robo

# Arquivos de entrada (dados brutos simulados)
ARQ_TELEMETRIA = DADOS_DIR / "telemetria.csv"
ARQ_LOGS_BORDO = DADOS_DIR / "logs_bordo.txt"

# Banco de dados (carga estruturada)
ARQ_BANCO = BASE_DIR / "missao.db"

# Artefatos finais gerados pelo robo
ARQ_RELATORIO_XLSX = SAIDA_DIR / "relatorio_missao.xlsx"
ARQ_RELATORIO_MD = SAIDA_DIR / "relatorio_missao.md"

# Arquivo de log da execucao
ARQ_LOG_EXEC = LOG_DIR / "estacao.log"

# ---------------------------------------------------------------------------
# Parametros da simulacao da missao
# ---------------------------------------------------------------------------
MISSAO_ID = "ARTEMIS-LX1"           # identificador da missao
QTD_LEITURAS = 2000                 # quantidade de leituras de telemetria
QTD_LOGS = 400                      # quantidade de linhas de log de bordo
INTERVALO_SEGUNDOS = 5              # intervalo entre leituras (telemetria)
SEMENTE = 42                        # semente aleatoria (resultados reproduziveis)

# Subsistemas de bordo monitorados
SUBSISTEMAS = ["ENERGIA", "NAVEGACAO", "COMUNICACAO", "TERMICO", "PROPULSAO"]

# ---------------------------------------------------------------------------
# Limites operacionais (engenharia) para cada parametro de telemetria.
#
# Cada parametro tem:
#   "nominal" -> (media, desvio) usados para gerar e analisar os dados
#   "limites" -> (minimo, maximo) seguros; fora disso e' anomalia critica
#   "unidade" -> unidade de medida (para os relatorios)
# ---------------------------------------------------------------------------
PARAMETROS = {
    "temperatura_c": {"nominal": (22.0, 6.0), "limites": (-30.0, 60.0), "unidade": "C"},
    "pressao_kpa": {"nominal": (101.3, 4.0), "limites": (80.0, 120.0), "unidade": "kPa"},
    "bateria_pct": {"nominal": (78.0, 9.0), "limites": (20.0, 100.0), "unidade": "%"},
    "velocidade_kms": {"nominal": (7.66, 0.08), "limites": (7.30, 8.00), "unidade": "km/s"},
    "altitude_km": {"nominal": (408.0, 6.0), "limites": (380.0, 440.0), "unidade": "km"},
    "radiacao_msv": {"nominal": (0.35, 0.10), "limites": (0.00, 0.80), "unidade": "mSv"},
    "sinal_dbm": {"nominal": (-72.0, 7.0), "limites": (-100.0, -50.0), "unidade": "dBm"},
}

# Lista pratica com o nome das colunas numericas de telemetria
COLUNAS_TELEMETRIA = list(PARAMETROS.keys())

# Limite estatistico: quantos desvios-padrao definem uma anomalia (z-score)
LIMITE_ZSCORE = 3.0

# Intervalo (segundos) entre execucoes quando o robo roda agendado
INTERVALO_AGENDAMENTO_MIN = 10
