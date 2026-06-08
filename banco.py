"""
banco.py
-----------------------------------------------------------------------------
ETAPA 4 do robo -- Carga de dados estruturados no banco (SQLite).

Persiste os dados ja processados e analisados em um banco SQLite, criando
tres tabelas: telemetria, anomalias e logs_bordo. Esse banco e' a fonte de
dados consumida depois pela API REST.

Topico do semestre aplicado: banco de dados com sqlite3.
Seguimos a recomendacao do professor de usar placeholders '?' para evitar
SQL Injection.
"""

import logging
import sqlite3

import config

logger = logging.getLogger("estacao.banco")


def conectar():
    """Abre uma conexao com o banco SQLite da missao."""
    return sqlite3.connect(config.ARQ_BANCO)


def criar_tabelas(conexao):
    """Cria as tabelas (apaga as anteriores para uma carga limpa por execucao)."""
    cursor = conexao.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS telemetria;
        DROP TABLE IF EXISTS anomalias;
        DROP TABLE IF EXISTS logs_bordo;

        CREATE TABLE telemetria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            missao_id TEXT NOT NULL,
            temperatura_c REAL,
            pressao_kpa REAL,
            bateria_pct REAL,
            velocidade_kms REAL,
            altitude_km REAL,
            radiacao_msv REAL,
            sinal_dbm REAL
        );

        CREATE TABLE anomalias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            parametro TEXT NOT NULL,
            valor REAL,
            media REAL,
            z_score REAL,
            metodo TEXT,
            severidade TEXT,
            unidade TEXT
        );

        CREATE TABLE logs_bordo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            nivel TEXT NOT NULL,
            subsistema TEXT,
            mensagem TEXT
        );
        """
    )
    conexao.commit()
    logger.info("Tabelas criadas no banco %s.", config.ARQ_BANCO.name)


def inserir_telemetria(conexao, df_telemetria):
    """Insere todas as leituras de telemetria usando placeholders '?'."""
    cursor = conexao.cursor()
    colunas = ["timestamp", "missao_id"] + config.COLUNAS_TELEMETRIA
    dados = [
        tuple(
            str(linha["timestamp"]) if c == "timestamp" else linha[c]
            for c in colunas
        )
        for _, linha in df_telemetria.iterrows()
    ]
    marcadores = ", ".join("?" for _ in colunas)
    sql = f"INSERT INTO telemetria ({', '.join(colunas)}) VALUES ({marcadores})"
    cursor.executemany(sql, dados)
    conexao.commit()
    logger.info("Inseridas %d leituras de telemetria.", len(dados))


def inserir_anomalias(conexao, df_anomalias):
    """Insere as anomalias detectadas."""
    if df_anomalias.empty:
        logger.info("Nenhuma anomalia para inserir.")
        return
    cursor = conexao.cursor()
    colunas = ["timestamp", "parametro", "valor", "media",
               "z_score", "metodo", "severidade", "unidade"]
    dados = [
        tuple(
            str(linha["timestamp"]) if c == "timestamp" else linha[c]
            for c in colunas
        )
        for _, linha in df_anomalias.iterrows()
    ]
    marcadores = ", ".join("?" for _ in colunas)
    sql = f"INSERT INTO anomalias ({', '.join(colunas)}) VALUES ({marcadores})"
    cursor.executemany(sql, dados)
    conexao.commit()
    logger.info("Inseridas %d anomalias.", len(dados))


def inserir_logs(conexao, df_logs):
    """Insere os logs de bordo estruturados."""
    if df_logs.empty:
        logger.info("Nenhum log para inserir.")
        return
    cursor = conexao.cursor()
    colunas = ["timestamp", "nivel", "subsistema", "mensagem"]
    dados = [
        tuple(
            str(linha["timestamp"]) if c == "timestamp" else linha[c]
            for c in colunas
        )
        for _, linha in df_logs.iterrows()
    ]
    marcadores = ", ".join("?" for _ in colunas)
    sql = f"INSERT INTO logs_bordo ({', '.join(colunas)}) VALUES ({marcadores})"
    cursor.executemany(sql, dados)
    conexao.commit()
    logger.info("Inseridos %d logs de bordo.", len(dados))


def carregar_tudo(df_telemetria, df_anomalias, df_logs):
    """Executa a etapa 4 completa: cria as tabelas e carrega os dados."""
    logger.info("== Etapa 4: carga dos dados no banco SQLite ==")
    conexao = conectar()
    try:
        criar_tabelas(conexao)
        inserir_telemetria(conexao, df_telemetria)
        inserir_anomalias(conexao, df_anomalias)
        inserir_logs(conexao, df_logs)
    except sqlite3.Error as erro:
        conexao.rollback()
        logger.error("Erro no banco de dados, alteracoes desfeitas: %s", erro)
        raise
    finally:
        conexao.close()
    logger.info("Carga no banco concluida com sucesso.")


if __name__ == "__main__":
    import processador
    import analise
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    tele, logs = processador.processar_tudo()
    anomalias, _, _ = analise.analisar_tudo(tele, logs)
    carregar_tudo(tele, anomalias, logs)
