"""
model.py
-----------------------------------------------------------------------------
Camada de Modelo da API (padrao MVC visto na disciplina).

Define os modelos de dados (Pydantic) e a classe Repository, que concentra
todo o acesso ao banco SQLite. Manter o acesso ao banco isolado aqui deixa
o controlador (api.py) limpo e facil de manter.
"""

import sqlite3

from pydantic import BaseModel

import config


# ---------------------------------------------------------------------------
# Modelos de resposta (Pydantic) -- documentam a API automaticamente no /docs
# ---------------------------------------------------------------------------
class Resumo(BaseModel):
    missao_id: str
    total_leituras: int
    total_anomalias: int
    anomalias_criticas: int
    eventos_criticos_log: int
    indice_saude: float
    status_missao: str


class Anomalia(BaseModel):
    timestamp: str
    parametro: str
    valor: float
    z_score: float
    metodo: str
    severidade: str
    unidade: str


# ---------------------------------------------------------------------------
# Repositorio -- acesso ao banco com sqlite3 e placeholders '?'
# ---------------------------------------------------------------------------
class Repository:
    """Concentra as consultas ao banco da missao."""

    def __init__(self, caminho_banco=None):
        self.caminho_banco = str(caminho_banco or config.ARQ_BANCO)

    def _conectar(self):
        conexao = sqlite3.connect(self.caminho_banco)
        # row_factory permite acessar colunas pelo nome (dict-like)
        conexao.row_factory = sqlite3.Row
        return conexao

    def resumo(self):
        """Calcula os indicadores principais direto do banco."""
        conexao = self._conectar()
        try:
            cur = conexao.cursor()
            total_leituras = cur.execute(
                "SELECT COUNT(*) FROM telemetria"
            ).fetchone()[0]
            total_anomalias = cur.execute(
                "SELECT COUNT(*) FROM anomalias"
            ).fetchone()[0]
            criticas = cur.execute(
                "SELECT COUNT(*) FROM anomalias WHERE severidade = ?",
                ("CRITICA",),
            ).fetchone()[0]
            eventos_log = cur.execute(
                "SELECT COUNT(*) FROM logs_bordo WHERE nivel IN (?, ?)",
                ("ERROR", "CRITICAL"),
            ).fetchone()[0]
            missao = cur.execute(
                "SELECT missao_id FROM telemetria LIMIT 1"
            ).fetchone()
        finally:
            conexao.close()

        # Reaproveita o mesmo calculo de indice de saude usado pelo robo
        indice, status = self._calcular_saude(
            total_leituras, total_anomalias, eventos_log
        )
        return {
            "missao_id": missao[0] if missao else config.MISSAO_ID,
            "total_leituras": total_leituras,
            "total_anomalias": total_anomalias,
            "anomalias_criticas": criticas,
            "eventos_criticos_log": eventos_log,
            "indice_saude": indice,
            "status_missao": status,
        }

    @staticmethod
    def _calcular_saude(total_leituras, total_anomalias, eventos_log):
        indice = 100.0
        indice -= min(40.0, eventos_log * 0.9)
        if total_leituras > 0:
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

    def listar_anomalias(self, limite=100, severidade=None):
        """Lista anomalias, com filtro opcional por severidade."""
        conexao = self._conectar()
        try:
            cur = conexao.cursor()
            if severidade:
                linhas = cur.execute(
                    "SELECT timestamp, parametro, valor, z_score, metodo, "
                    "severidade, unidade FROM anomalias WHERE severidade = ? "
                    "ORDER BY timestamp LIMIT ?",
                    (severidade, limite),
                ).fetchall()
            else:
                linhas = cur.execute(
                    "SELECT timestamp, parametro, valor, z_score, metodo, "
                    "severidade, unidade FROM anomalias ORDER BY timestamp LIMIT ?",
                    (limite,),
                ).fetchall()
        finally:
            conexao.close()
        return [dict(linha) for linha in linhas]

    def listar_telemetria(self, limite=100):
        """Lista as ultimas leituras de telemetria."""
        conexao = self._conectar()
        try:
            cur = conexao.cursor()
            linhas = cur.execute(
                "SELECT timestamp, temperatura_c, pressao_kpa, bateria_pct, "
                "velocidade_kms, altitude_km, radiacao_msv, sinal_dbm "
                "FROM telemetria ORDER BY timestamp LIMIT ?",
                (limite,),
            ).fetchall()
        finally:
            conexao.close()
        return [dict(linha) for linha in linhas]

    def logs_por_nivel(self):
        """Conta os logs de bordo agrupados por nivel de severidade."""
        conexao = self._conectar()
        try:
            cur = conexao.cursor()
            linhas = cur.execute(
                "SELECT nivel, COUNT(*) AS quantidade FROM logs_bordo "
                "GROUP BY nivel ORDER BY quantidade DESC"
            ).fetchall()
        finally:
            conexao.close()
        return [dict(linha) for linha in linhas]
