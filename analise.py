"""
analise.py
-----------------------------------------------------------------------------
ETAPA 3 do robo -- Inteligencia de dados / algoritmos de analise.

Aqui mora a "inteligencia" da solucao. Aplicamos algoritmos de analise para
extrair valor dos dados brutos:

  1. Deteccao de anomalias na telemetria, por dois metodos combinados:
       * ESTATISTICO  -> z-score (valor muito distante da media, |z| > 3)
       * ENGENHARIA   -> valor fora dos limites operacionais seguros
  2. Classificacao dos logs de bordo por severidade e subsistema, com um
     calculo de "indice de saude" da missao.

Criterio atendido: "Inteligencia de Dados e Recursos de IA" (algoritmos de
analise para processar e extrair valor de dados complexos).
"""

import logging

import pandas as pd

import config

logger = logging.getLogger("estacao.analise")

# Severidade numerica de cada nivel de log (para calcular indice de saude)
PESO_NIVEL = {"INFO": 0, "WARNING": 1, "ERROR": 3, "CRITICAL": 5}

# Dicionario de temas para a classificacao NLP (por palavras-chave) das
# mensagens de log. E' uma abordagem simples de processamento de linguagem
# natural: normaliza o texto e o associa a um tema tecnico pela ocorrencia de
# termos caracteristicos, agregando o "assunto" recorrente da missao.
TEMAS_LOG = {
    "ENERGIA": ["bateria", "energia", "solar", "consumo", "painel"],
    "TERMICO": ["temperatura", "termico", "modulo", "calor"],
    "COMUNICACAO": ["sinal", "comunicacao", "transmissao", "pacote", "telemetria"],
    "NAVEGACAO": ["rota", "atitude", "desvio", "controle", "orientado"],
    "RADIACAO": ["radiacao", "pico"],
    "MANUTENCAO": ["sensor", "reinicializacao", "subsistema", "falha",
                   "checagem", "rotina", "sincronizacao", "relogio"],
}


def classificar_mensagem(mensagem):
    """
    Classifica uma mensagem de log em um tema tecnico (NLP por palavras-chave).

    Normaliza o texto (minusculas) e devolve o primeiro tema cujo termo
    caracteristico aparece na mensagem; 'OUTROS' se nenhum casar.
    """
    texto = str(mensagem).lower()
    for tema, termos in TEMAS_LOG.items():
        if any(termo in texto for termo in termos):
            return tema
    return "OUTROS"


def detectar_anomalias(df_telemetria):
    """
    Detecta anomalias em cada parametro numerico da telemetria.

    Devolve um DataFrame com uma linha por anomalia encontrada, contendo:
    timestamp, parametro, valor, media, z_score, metodo e severidade.
    """
    if df_telemetria.empty:
        logger.warning("Telemetria vazia: nenhuma anomalia a detectar.")
        return pd.DataFrame()

    anomalias = []
    for parametro in config.COLUNAS_TELEMETRIA:
        serie = df_telemetria[parametro]
        minimo, maximo = config.PARAMETROS[parametro]["limites"]

        # Baseline robusto: a media/desvio de referencia sao calculados apenas
        # com as leituras DENTRO dos limites, para que valores absurdos (fora
        # de escala) nao distorcam a estatistica e mascarem desvios sutis.
        base = serie[serie.between(minimo, maximo)]
        media = base.mean() if not base.empty else serie.mean()
        desvio = base.std() if not base.empty else serie.std()

        # z-score de cada leitura (evita divisao por zero se desvio == 0)
        if desvio and desvio > 0:
            z = (serie - media) / desvio
        else:
            z = serie * 0

        for idx, valor in serie.items():
            z_valor = float(z.loc[idx])
            fora_estatistico = abs(z_valor) > config.LIMITE_ZSCORE
            fora_engenharia = valor < minimo or valor > maximo

            if not (fora_estatistico or fora_engenharia):
                continue

            # Define o metodo e a severidade da anomalia
            if fora_engenharia:
                metodo = "ENGENHARIA"
                severidade = "CRITICA"
            else:
                metodo = "ESTATISTICO"
                severidade = "ALTA" if abs(z_valor) > 4 else "MEDIA"

            anomalias.append({
                "timestamp": df_telemetria.loc[idx, "timestamp"],
                "parametro": parametro,
                "valor": round(float(valor), 3),
                "media": round(float(media), 3),
                "z_score": round(z_valor, 2),
                "metodo": metodo,
                "severidade": severidade,
                "unidade": config.PARAMETROS[parametro]["unidade"],
            })

    df_anomalias = pd.DataFrame(anomalias)
    if not df_anomalias.empty:
        df_anomalias = df_anomalias.sort_values("timestamp").reset_index(drop=True)

    logger.info("Deteccao concluida: %d anomalias encontradas.", len(df_anomalias))
    return df_anomalias


def classificar_logs(df_logs):
    """
    Classifica os logs de bordo agregando por nivel e por subsistema.

    Devolve um dicionario com:
      * por_nivel       -> contagem por severidade
      * por_subsistema  -> contagem por subsistema
      * por_tema        -> contagem por tema (classificacao NLP das mensagens)
      * eventos_criticos-> lista dos logs ERROR/CRITICAL
    """
    if df_logs.empty:
        logger.warning("Nenhum log para classificar.")
        return {"por_nivel": {}, "por_subsistema": {},
                "por_tema": {}, "eventos_criticos": []}

    por_nivel = df_logs["nivel"].value_counts().to_dict()
    por_subsistema = df_logs["subsistema"].value_counts().to_dict()

    # Classificacao NLP por palavras-chave: agrega o "assunto" das mensagens
    temas = df_logs["mensagem"].apply(classificar_mensagem)
    por_tema = temas.value_counts().to_dict()

    criticos = df_logs[df_logs["nivel"].isin(["ERROR", "CRITICAL"])]
    eventos_criticos = criticos.to_dict(orient="records")

    logger.info("Logs classificados: %d eventos criticos (ERROR/CRITICAL); "
                "temas predominantes: %s.",
                len(eventos_criticos),
                ", ".join(list(por_tema)[:3]) or "-")
    return {
        "por_nivel": por_nivel,
        "por_subsistema": por_subsistema,
        "por_tema": por_tema,
        "eventos_criticos": eventos_criticos,
    }


def indice_saude(contagem_niveis, total_anomalias, total_leituras):
    """
    Funcao CANONICA do indice de saude (0 a 100).

    Recebe apenas valores primitivos (uma contagem de logs por nivel e os
    totais de anomalias/leituras) justamente para poder ser reutilizada tanto
    pelo robo (a partir dos DataFrames) quanto pela API (a partir do banco),
    garantindo que os dois calculem o indice EXATAMENTE da mesma forma.

    Parte de 100 e penaliza conforme a gravidade dos logs e a proporcao de
    anomalias na telemetria. E' um indicador acionavel para o controle.
    """
    indice = 100.0

    # Penalidade pelos logs, ponderada pela severidade de cada nivel
    penalidade_logs = sum(PESO_NIVEL.get(nivel, 0) * qtd
                          for nivel, qtd in contagem_niveis.items())
    indice -= min(40.0, penalidade_logs * 0.3)

    # Penalidade pela proporcao de anomalias na telemetria
    if total_leituras > 0 and total_anomalias > 0:
        proporcao = total_anomalias / total_leituras
        indice -= min(40.0, proporcao * 100 * 2)

    indice = max(0.0, round(indice, 1))

    if indice >= 80:
        status = "NOMINAL"
    elif indice >= 50:
        status = "ATENCAO"
    else:
        status = "CRITICO"

    return indice, status


def calcular_indice_saude(df_logs, df_anomalias, total_leituras):
    """
    Calcula o indice de saude a partir dos DataFrames do robo.

    E' um envelope fino sobre 'indice_saude': extrai a contagem de logs por
    nivel e delega o calculo para a funcao canonica.
    """
    contagem_niveis = (
        df_logs["nivel"].value_counts().to_dict() if not df_logs.empty else {}
    )
    indice, status = indice_saude(
        contagem_niveis, len(df_anomalias), total_leituras
    )
    logger.info("Indice de saude da missao: %.1f (%s).", indice, status)
    return indice, status


def analisar_tudo(df_telemetria, df_logs):
    """
    Executa a etapa 3 completa.

    Devolve (df_anomalias, classificacao_logs, resumo) onde 'resumo' agrega
    os principais indicadores da missao.
    """
    logger.info("== Etapa 3: analise inteligente dos dados ==")
    df_anomalias = detectar_anomalias(df_telemetria)
    classificacao = classificar_logs(df_logs)
    indice, status = calcular_indice_saude(df_logs, df_anomalias, len(df_telemetria))

    resumo = {
        "missao_id": config.MISSAO_ID,
        "total_leituras": int(len(df_telemetria)),
        "total_logs": int(len(df_logs)),
        "total_anomalias": int(len(df_anomalias)),
        "anomalias_criticas": int(
            (df_anomalias["severidade"] == "CRITICA").sum()
        ) if not df_anomalias.empty else 0,
        "eventos_criticos_log": len(classificacao["eventos_criticos"]),
        "indice_saude": indice,
        "status_missao": status,
    }
    return df_anomalias, classificacao, resumo


if __name__ == "__main__":
    import processador
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    tele, logs = processador.processar_tudo()
    anomalias, classificacao, resumo = analisar_tudo(tele, logs)
    print(resumo)
