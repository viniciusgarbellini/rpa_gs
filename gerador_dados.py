"""
gerador_dados.py
-----------------------------------------------------------------------------
ETAPA 1 do robo -- Ingestao / geracao dos dados brutos da missao.

Como nao temos acesso real a uma nave, este modulo SIMULA os dados que uma
missao espacial geraria:

  * telemetria.csv   -> leituras numericas dos sensores de bordo
  * logs_bordo.txt   -> mensagens de texto dos sistemas (estilo log)

A simulacao injeta DE PROPOSITO algumas anomalias (picos de radiacao, queda
de bateria, etc.) para que as etapas seguintes de analise tenham o que
detectar -- exatamente como aconteceria numa missao real.

Topico do semestre aplicado: manipulacao de arquivos (escrita de CSV/TXT).
"""

import csv
import logging
import random
from datetime import datetime, timedelta

import config

logger = logging.getLogger("estacao.gerador")


def _gerar_linha_telemetria(momento, rng):
    """Gera uma unica leitura de telemetria (um dicionario)."""
    leitura = {
        "timestamp": momento.strftime("%Y-%m-%d %H:%M:%S"),
        "missao_id": config.MISSAO_ID,
    }
    # Cada parametro e' gerado em torno da media nominal com um pouco de ruido
    for nome, info in config.PARAMETROS.items():
        media, desvio = info["nominal"]
        valor = rng.gauss(media, desvio)
        leitura[nome] = round(valor, 3)
    return leitura


def _injetar_anomalias(leituras, rng):
    """
    Injeta anomalias propositais em ~3% das leituras para tornar a analise
    realista. Sao criados DOIS tipos de anomalia, para exercitar os dois
    metodos de deteccao da etapa de analise:

      * CRITICA (engenharia) -> valor estoura os limites operacionais seguros.
      * ESTATISTICA          -> valor continua DENTRO dos limites, mas muito
        distante da media (desvio de varios sigmas), so detectavel por z-score.
    """
    qtd_anomalias = max(1, int(len(leituras) * 0.03))
    indices = rng.sample(range(len(leituras)), qtd_anomalias)

    criticas = 0
    estatisticas = 0
    for i in indices:
        parametro = rng.choice(config.COLUNAS_TELEMETRIA)
        media, desvio = config.PARAMETROS[parametro]["nominal"]
        minimo, maximo = config.PARAMETROS[parametro]["limites"]

        if rng.random() < 0.55:
            # Anomalia critica: ultrapassa um dos limites seguros
            if rng.random() < 0.5:
                leituras[i][parametro] = round(minimo - abs(minimo * 0.25) - 5, 3)
            else:
                leituras[i][parametro] = round(maximo + abs(maximo * 0.25) + 5, 3)
            criticas += 1
        else:
            # Anomalia estatistica: desvio de 3.3 a 4.6 sigmas, mas dentro
            # dos limites. Escolhe o lado que cabe dentro da faixa segura.
            fator = rng.uniform(3.3, 4.6)
            candidatos = [media + fator * desvio, media - fator * desvio]
            rng.shuffle(candidatos)
            valor = next((c for c in candidatos if minimo < c < maximo), None)
            if valor is None:
                # Sem espaco dentro dos limites: vira anomalia critica
                leituras[i][parametro] = round(maximo + abs(maximo * 0.25) + 5, 3)
                criticas += 1
            else:
                leituras[i][parametro] = round(valor, 3)
                estatisticas += 1

    logger.info("Injetadas %d anomalias propositais (%d criticas, %d estatisticas).",
                qtd_anomalias, criticas, estatisticas)
    return leituras


def gerar_telemetria():
    """Gera o arquivo telemetria.csv com QTD_LEITURAS leituras."""
    rng = random.Random(config.SEMENTE)
    inicio = datetime(2026, 6, 1, 8, 0, 0)

    leituras = []
    for i in range(config.QTD_LEITURAS):
        momento = inicio + timedelta(seconds=i * config.INTERVALO_SEGUNDOS)
        leituras.append(_gerar_linha_telemetria(momento, rng))

    leituras = _injetar_anomalias(leituras, rng)

    config.DADOS_DIR.mkdir(parents=True, exist_ok=True)
    cabecalho = ["timestamp", "missao_id"] + config.COLUNAS_TELEMETRIA
    try:
        with open(config.ARQ_TELEMETRIA, "w", newline="", encoding="utf-8") as arq:
            escritor = csv.DictWriter(arq, fieldnames=cabecalho)
            escritor.writeheader()
            escritor.writerows(leituras)
    except OSError as erro:
        logger.error("Falha ao escrever telemetria: %s", erro)
        raise

    logger.info("Telemetria gerada: %s (%d leituras).",
                config.ARQ_TELEMETRIA.name, len(leituras))
    return config.ARQ_TELEMETRIA


def gerar_logs_bordo():
    """Gera o arquivo logs_bordo.txt com mensagens de sistema."""
    rng = random.Random(config.SEMENTE + 1)
    inicio = datetime(2026, 6, 1, 8, 0, 0)

    # Mensagens-modelo por nivel de severidade
    modelos = {
        "INFO": [
            "Checagem de rotina concluida com sucesso",
            "Sincronizacao de relogio com base terrestre OK",
            "Painel solar orientado para captacao maxima",
            "Pacote de telemetria transmitido",
        ],
        "WARNING": [
            "Temperatura do modulo acima do esperado",
            "Sinal de comunicacao oscilando",
            "Consumo de energia acima da media",
            "Pequeno desvio de rota detectado",
        ],
        "ERROR": [
            "Falha temporaria no sensor",
            "Perda de pacote na transmissao",
            "Reinicializacao de subsistema necessaria",
        ],
        "CRITICAL": [
            "Bateria em nivel critico",
            "Pico de radiacao detectado",
            "Perda de controle de atitude",
        ],
    }
    # Pesos: a maioria das mensagens e' INFO; criticos sao raros
    niveis = ["INFO", "WARNING", "ERROR", "CRITICAL"]
    pesos = [70, 18, 9, 3]

    config.DADOS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(config.ARQ_LOGS_BORDO, "w", encoding="utf-8") as arq:
            for i in range(config.QTD_LOGS):
                momento = inicio + timedelta(seconds=i * 25)
                nivel = rng.choices(niveis, weights=pesos, k=1)[0]
                subsistema = rng.choice(config.SUBSISTEMAS)
                mensagem = rng.choice(modelos[nivel])
                linha = (f"{momento.strftime('%Y-%m-%d %H:%M:%S')} "
                         f"[{nivel}] {subsistema}: {mensagem}")
                arq.write(linha + "\n")
    except OSError as erro:
        logger.error("Falha ao escrever logs de bordo: %s", erro)
        raise

    logger.info("Logs de bordo gerados: %s (%d linhas).",
                config.ARQ_LOGS_BORDO.name, config.QTD_LOGS)
    return config.ARQ_LOGS_BORDO


def gerar_todos():
    """Gera os dois arquivos de entrada da missao."""
    logger.info("== Etapa 1: gerando dados brutos da missao ==")
    gerar_telemetria()
    gerar_logs_bordo()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    gerar_todos()
