"""
api.py
-----------------------------------------------------------------------------
ETAPA 6 do robo -- API REST (camada Controller, padrao MVC).

Expoe os dados ja processados e analisados pelo robo atraves de uma API REST
feita com FastAPI. E' essa API que alimenta o front-end (dashboard) com dados
estruturados.

Topico do semestre aplicado: APIs REST com FastAPI + Pydantic + SQLite.

Como executar:
    python api.py
    # depois acesse http://localhost:8000/docs  (documentacao automatica)
"""

import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

import config
from model import Anomalia, Repository, Resumo

logger = logging.getLogger("estacao.api")

app = FastAPI(
    title="Estacao de Controle de Missao - API",
    description="API REST que serve a telemetria, anomalias e logs "
                "processados pelo robo RPA.",
    version="1.0.0",
)

# Libera o acesso do front-end (CORS), como visto na aula de REST API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

repositorio = Repository()


@app.get("/api", include_in_schema=False)
def raiz_api():
    """Redireciona a raiz da API para a documentacao automatica."""
    return RedirectResponse(url="/docs")


@app.get("/resumo", tags=["Missao"], response_model=Resumo)
def obter_resumo():
    """Indicadores principais da missao (status, indice de saude, totais)."""
    try:
        return repositorio.resumo()
    except Exception as erro:
        logger.error("Erro ao obter resumo: %s", erro)
        raise HTTPException(status_code=500,
                            detail="Banco indisponivel. Rode o robo primeiro.")


@app.get("/anomalias", tags=["Analise"], response_model=list[Anomalia])
def obter_anomalias(limite: int = 100, severidade: str | None = None):
    """Lista as anomalias detectadas (filtro opcional por severidade)."""
    try:
        return repositorio.listar_anomalias(limite=limite, severidade=severidade)
    except Exception as erro:
        logger.error("Erro ao listar anomalias: %s", erro)
        raise HTTPException(status_code=500,
                            detail="Banco indisponivel. Rode o robo primeiro.")


@app.get("/telemetria", tags=["Dados"])
def obter_telemetria(limite: int = 100):
    """Lista as leituras de telemetria estruturadas."""
    try:
        return repositorio.listar_telemetria(limite=limite)
    except Exception as erro:
        logger.error("Erro ao listar telemetria: %s", erro)
        raise HTTPException(status_code=500,
                            detail="Banco indisponivel. Rode o robo primeiro.")


@app.get("/logs/niveis", tags=["Analise"])
def obter_logs_por_nivel():
    """Contagem dos logs de bordo por nivel de severidade."""
    try:
        return repositorio.logs_por_nivel()
    except Exception as erro:
        logger.error("Erro ao agrupar logs: %s", erro)
        raise HTTPException(status_code=500,
                            detail="Banco indisponivel. Rode o robo primeiro.")


@app.get("/logs/temas", tags=["Analise"])
def obter_logs_por_tema():
    """Temas recorrentes nas mensagens de log (classificacao NLP)."""
    try:
        return repositorio.logs_por_tema()
    except Exception as erro:
        logger.error("Erro ao classificar temas: %s", erro)
        raise HTTPException(status_code=500,
                            detail="Banco indisponivel. Rode o robo primeiro.")


# Servir o front-end (dashboard) na raiz "/".
# Fica por ultimo para nao "engolir" as rotas da API definidas acima.
PASTA_FRONT = config.BASE_DIR / "frontend"
if PASTA_FRONT.exists():
    app.mount("/", StaticFiles(directory=str(PASTA_FRONT), html=True), name="front")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
