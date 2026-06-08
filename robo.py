"""
robo.py
-----------------------------------------------------------------------------
ORQUESTRADOR do robo RPA -- executa o fluxo de ponta a ponta.

Este e' o "cerebro" da automacao: ele encadeia, na ordem certa, todas as
etapas do pipeline e cuida do tratamento de erros e do registro (logging)
de tudo o que acontece. Cada etapa e' isolada num try/except para que uma
falha seja registrada de forma clara, sem deixar o robo em estado inconsistente.

Fluxo (RPA de ponta a ponta):
    1. Gera os dados brutos da missao        (gerador_dados)
    2. Le e estrutura com pandas             (processador)
    3. Analisa: anomalias + classificacao    (analise)
    4. Carrega no banco SQLite               (banco)
    5. Gera os artefatos (Excel e relatorio) (relatorio)

Criterio atendido: "Arquitetura de Fluxo e Engenharia de Software"
(robustez do fluxo, tratamento de excecoes e qualidade do codigo).
"""

import logging
import sys

import config
import gerador_dados
import processador
import analise
import banco
import relatorio


def configurar_logging():
    """
    Configura o logging para escrever ao mesmo tempo no console e em arquivo.
    Centralizar isso aqui garante rastreabilidade de toda a execucao do robo.
    """
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger_raiz = logging.getLogger("estacao")
    logger_raiz.setLevel(logging.INFO)
    logger_raiz.handlers.clear()  # evita handlers duplicados em re-execucoes

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formato)
    logger_raiz.addHandler(console)

    arquivo = logging.FileHandler(config.ARQ_LOG_EXEC, encoding="utf-8")
    arquivo.setFormatter(formato)
    logger_raiz.addHandler(arquivo)

    return logger_raiz


def executar():
    """
    Executa o pipeline completo do robo.

    Devolve o dicionario 'resumo' da missao em caso de sucesso, ou None se
    alguma etapa falhar (a falha e' registrada no log).
    """
    logger = logging.getLogger("estacao.robo")
    logger.info("################################################")
    logger.info("# INICIANDO ROBO -- Estacao de Controle de Missao")
    logger.info("################################################")

    try:
        # Etapa 1 -- Ingestao / geracao dos dados
        gerador_dados.gerar_todos()

        # Etapa 2 -- Processamento com pandas
        df_telemetria, df_logs = processador.processar_tudo()

        # Etapa 3 -- Analise inteligente
        df_anomalias, classificacao, resumo = analise.analisar_tudo(
            df_telemetria, df_logs
        )

        # Etapa 4 -- Carga no banco
        banco.carregar_tudo(df_telemetria, df_anomalias, df_logs)

        # Etapa 5 -- Artefatos
        relatorio.gerar_todos(
            df_telemetria, df_anomalias, df_logs, classificacao, resumo
        )

    except FileNotFoundError as erro:
        logger.error("Arquivo necessario nao encontrado: %s", erro)
        return None
    except Exception as erro:  # rede de seguranca: nada derruba o robo silenciosamente
        logger.exception("Falha inesperada na execucao do robo: %s", erro)
        return None

    logger.info("------------------------------------------------")
    logger.info("ROBO FINALIZADO COM SUCESSO")
    logger.info("Status da missao: %s | Indice de saude: %s",
                resumo["status_missao"], resumo["indice_saude"])
    logger.info("Artefatos em: %s", config.SAIDA_DIR)
    logger.info("------------------------------------------------")
    return resumo


if __name__ == "__main__":
    configurar_logging()
    resultado = executar()
    # Codigo de saida: 0 = sucesso, 1 = falha (util para agendamento/Docker)
    sys.exit(0 if resultado else 1)
