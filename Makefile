.EXPORT_ALL_VARIABLES:

COMPOSE_CONVERT_WINDOWS_PATHS=1

install:
	pip install -r requirements.txt
	pip install -r code/models/requirements.txt
	chmod 666 /var/run/docker.sock

start:
	docker compose up --build

stop:
	docker compose down -v

airflow-import:
	docker exec -it airflow-scheduler airflow variables import variables.json && \
	airflow connections import connections.json && \
	exit
