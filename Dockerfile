# Dockerfile -- empacota a Estacao de Controle de Missao em um container.
# Topico do semestre aplicado: containers e Docker.
#
# Build:  docker build -t estacao-missao .
# Run:    docker run -p 8000:8000 estacao-missao

FROM python:3.12-slim

# Evita arquivos .pyc e deixa o log do Python sair em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependencias primeiro (aproveita o cache de camadas do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo do projeto
COPY . .

# Roda o robo uma vez (gera dados + banco + artefatos) e sobe a API.
# Assim o container ja inicia com dados prontos para o front-end consumir.
EXPOSE 8000
CMD ["sh", "-c", "python robo.py && python api.py"]
