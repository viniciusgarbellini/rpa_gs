"""
processador.py
-----------------------------------------------------------------------------
ETAPA 2 do robo -- Processamento e estruturacao dos dados com pandas.

Le os arquivos brutos (CSV de telemetria e TXT de logs), limpa, valida e
estrutura tudo em DataFrames prontos para analise.

Topicos do semestre aplicados:
  * manipulacao de arquivos (pandas.read_csv, leitura de texto)
  * analise de dados (limpeza, tipos, parsing com DataFrame)
"""

import logging
import re

import pandas as pd

import config

logger = logging.getLogger("estacao.processador")

# Regex para extrair os campos de cada linha de log de bordo:
# 2026-06-01 08:00:00 [WARNING] TERMICO: mensagem...
PADRAO_LOG = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\[(?P<nivel>\w+)\] (?P<subsistema>\w+): (?P<mensagem>.+)$"
)


def carregar_telemetria():
    """
    Le telemetria.csv e devolve um DataFrame limpo e validado.
    """
    if not config.ARQ_TELEMETRIA.exists():
        raise FileNotFoundError(
            f"Arquivo de telemetria nao encontrado: {config.ARQ_TELEMETRIA}"
        )

    try:
        df = pd.read_csv(config.ARQ_TELEMETRIA, parse_dates=["timestamp"])
    except (pd.errors.ParserError, ValueError) as erro:
        logger.error("Erro ao ler/parsear a telemetria: %s", erro)
        raise

    qtd_inicial = len(df)

    # Limpeza: remove leituras totalmente vazias e duplicadas
    df = df.dropna(how="all").drop_duplicates()

    # Garante que as colunas numericas sejam de fato numericas
    for coluna in config.COLUNAS_TELEMETRIA:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    # Remove linhas que ficaram sem valor apos a conversao
    df = df.dropna(subset=config.COLUNAS_TELEMETRIA)
    df = df.sort_values("timestamp").reset_index(drop=True)

    logger.info("Telemetria processada: %d leituras validas (de %d brutas).",
                len(df), qtd_inicial)
    return df


def carregar_logs():
    """
    Le logs_bordo.txt linha a linha e devolve um DataFrame estruturado
    com as colunas: timestamp, nivel, subsistema, mensagem.
    """
    if not config.ARQ_LOGS_BORDO.exists():
        raise FileNotFoundError(
            f"Arquivo de logs nao encontrado: {config.ARQ_LOGS_BORDO}"
        )

    registros = []
    descartadas = 0
    with open(config.ARQ_LOGS_BORDO, "r", encoding="utf-8") as arq:
        for linha in arq:
            linha = linha.strip()
            if not linha:
                continue
            casamento = PADRAO_LOG.match(linha)
            if casamento:
                registros.append(casamento.groupdict())
            else:
                descartadas += 1

    if descartadas:
        logger.warning("%d linhas de log fora do padrao foram ignoradas.",
                       descartadas)

    df = pd.DataFrame(registros)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

    logger.info("Logs processados: %d registros estruturados.", len(df))
    return df


def processar_tudo():
    """Executa a etapa 2 completa e devolve (df_telemetria, df_logs)."""
    logger.info("== Etapa 2: processando e estruturando os dados ==")
    df_telemetria = carregar_telemetria()
    df_logs = carregar_logs()
    return df_telemetria, df_logs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    tele, logs = processar_tudo()
    print(tele.head())
    print(logs.head())
