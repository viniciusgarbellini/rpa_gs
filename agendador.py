"""
agendador.py
-----------------------------------------------------------------------------
ETAPA 8 do robo -- Agendamento da execucao automatica.

Um robo RPA de verdade nao roda so quando alguem manda: ele roda sozinho, de
tempos em tempos. Este modulo usa a biblioteca 'schedule' (vista na aula de
Tasks/Agendamento) para reexecutar o pipeline em intervalos regulares.

Topico do semestre aplicado: agendamento de scripts (schedule).

Como executar:
    python agendador.py
    # roda o robo uma vez na hora e, depois, a cada N minutos.
"""

import logging
import time

import schedule

import config
from robo import configurar_logging, executar


def tarefa_robo():
    """Tarefa agendada: executa o pipeline completo do robo."""
    logger = logging.getLogger("estacao.agendador")
    logger.info(">>> Disparo agendado: executando o robo <<<")
    executar()


def iniciar():
    """Configura o agendamento e mantem o robo rodando em laco."""
    configurar_logging()
    logger = logging.getLogger("estacao.agendador")

    intervalo = config.INTERVALO_AGENDAMENTO_MIN
    logger.info("Agendador iniciado. O robo rodara a cada %d minuto(s).", intervalo)

    # Roda uma vez imediatamente para ja ter dados, depois agenda as proximas
    tarefa_robo()
    schedule.every(intervalo).minutes.do(tarefa_robo)

    # Laco principal do agendador (padrao visto na aula)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Agendador encerrado pelo usuario.")


if __name__ == "__main__":
    iniciar()
