"""
relatorio.py
-----------------------------------------------------------------------------
ETAPA 5 do robo -- Geracao dos artefatos finais.

Produz, de forma automatica, os "produtos" que o robo entrega ao controle
da missao:

  * relatorio_missao.xlsx -> planilha com varias abas (telemetria, anomalias,
    logs, estatisticas e um resumo executivo), com formatacao basica.
  * relatorio_missao.md   -> relatorio consolidado em texto (Markdown),
    legivel por humanos.

Criterio atendido: "Entrega de Artefatos e Outputs Tecnicos" (estruturacao
de planilhas/DataFrames, arquivos gerados e relatorios consolidados).
"""

import logging

import pandas as pd

import config

logger = logging.getLogger("estacao.relatorio")


def _estatisticas_telemetria(df_telemetria):
    """Monta um DataFrame com estatisticas descritivas por parametro."""
    linhas = []
    for parametro in config.COLUNAS_TELEMETRIA:
        serie = df_telemetria[parametro]
        minimo, maximo = config.PARAMETROS[parametro]["limites"]
        linhas.append({
            "parametro": parametro,
            "unidade": config.PARAMETROS[parametro]["unidade"],
            "minimo": round(float(serie.min()), 3),
            "media": round(float(serie.mean()), 3),
            "maximo": round(float(serie.max()), 3),
            "desvio_padrao": round(float(serie.std()), 3),
            "limite_inf": minimo,
            "limite_sup": maximo,
        })
    return pd.DataFrame(linhas)


def gerar_excel(df_telemetria, df_anomalias, df_logs, resumo):
    """Gera a planilha Excel consolidada com varias abas."""
    config.SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    df_estat = _estatisticas_telemetria(df_telemetria)
    df_resumo = pd.DataFrame(
        [{"indicador": k, "valor": v} for k, v in resumo.items()]
    )

    try:
        with pd.ExcelWriter(config.ARQ_RELATORIO_XLSX, engine="openpyxl") as escritor:
            df_resumo.to_excel(escritor, sheet_name="Resumo", index=False)
            df_estat.to_excel(escritor, sheet_name="Estatisticas", index=False)
            df_anomalias.to_excel(escritor, sheet_name="Anomalias", index=False)
            df_logs.to_excel(escritor, sheet_name="Logs", index=False)
            df_telemetria.to_excel(escritor, sheet_name="Telemetria", index=False)
            _ajustar_largura_colunas(escritor)
    except OSError as erro:
        logger.error("Falha ao gerar a planilha Excel: %s", erro)
        raise

    logger.info("Planilha gerada: %s", config.ARQ_RELATORIO_XLSX.name)
    return config.ARQ_RELATORIO_XLSX


def _ajustar_largura_colunas(escritor):
    """Ajuste cosmetico: deixa as colunas das planilhas mais legiveis."""
    for planilha in escritor.book.worksheets:
        for coluna in planilha.columns:
            largura = 12
            letra = coluna[0].column_letter
            for celula in coluna:
                if celula.value is not None:
                    largura = max(largura, len(str(celula.value)) + 2)
            planilha.column_dimensions[letra].width = min(largura, 40)


def gerar_markdown(df_anomalias, classificacao, resumo):
    """Gera o relatorio consolidado em Markdown (legivel por humanos)."""
    config.SAIDA_DIR.mkdir(parents=True, exist_ok=True)

    linhas = []
    linhas.append(f"# Relatorio da Missao {resumo['missao_id']}")
    linhas.append("")
    linhas.append("> Relatorio gerado automaticamente pela "
                  "Estacao de Controle de Missao.")
    linhas.append("")
    linhas.append("## Resumo Executivo")
    linhas.append("")
    linhas.append(f"- **Status da missao:** {resumo['status_missao']}")
    linhas.append(f"- **Indice de saude:** {resumo['indice_saude']} / 100")
    linhas.append(f"- **Leituras de telemetria:** {resumo['total_leituras']}")
    linhas.append(f"- **Anomalias detectadas:** {resumo['total_anomalias']} "
                  f"(criticas: {resumo['anomalias_criticas']})")
    linhas.append(f"- **Eventos criticos no log:** {resumo['eventos_criticos_log']}")
    linhas.append("")

    # Anomalias por parametro
    linhas.append("## Anomalias por Parametro")
    linhas.append("")
    if df_anomalias.empty:
        linhas.append("Nenhuma anomalia detectada.")
    else:
        contagem = df_anomalias["parametro"].value_counts()
        linhas.append("| Parametro | Qtd | Severidade predominante |")
        linhas.append("|-----------|-----|-------------------------|")
        for parametro, qtd in contagem.items():
            sev = (df_anomalias[df_anomalias["parametro"] == parametro]
                   ["severidade"].mode().iloc[0])
            linhas.append(f"| {parametro} | {qtd} | {sev} |")
    linhas.append("")

    # Logs por nivel
    linhas.append("## Logs de Bordo por Severidade")
    linhas.append("")
    if classificacao["por_nivel"]:
        linhas.append("| Nivel | Quantidade |")
        linhas.append("|-------|------------|")
        for nivel, qtd in classificacao["por_nivel"].items():
            linhas.append(f"| {nivel} | {qtd} |")
    else:
        linhas.append("Nenhum log registrado.")
    linhas.append("")

    conteudo = "\n".join(linhas)
    try:
        with open(config.ARQ_RELATORIO_MD, "w", encoding="utf-8") as arq:
            arq.write(conteudo)
    except OSError as erro:
        logger.error("Falha ao gerar o relatorio Markdown: %s", erro)
        raise

    logger.info("Relatorio gerado: %s", config.ARQ_RELATORIO_MD.name)
    return config.ARQ_RELATORIO_MD


def gerar_todos(df_telemetria, df_anomalias, df_logs, classificacao, resumo):
    """Executa a etapa 5 completa: gera todos os artefatos."""
    logger.info("== Etapa 5: geracao dos artefatos (Excel e relatorio) ==")
    gerar_excel(df_telemetria, df_anomalias, df_logs, resumo)
    gerar_markdown(df_anomalias, classificacao, resumo)


if __name__ == "__main__":
    import processador
    import analise
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    tele, logs = processador.processar_tudo()
    anomalias, classificacao, resumo = analise.analisar_tudo(tele, logs)
    gerar_todos(tele, anomalias, logs, classificacao, resumo)
