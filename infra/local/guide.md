# Setting scooters environment locally

1. Проверьте, что у вас есть все пакеты для докера и он запущен у вас локально (sudo systemctl status docker). Если нет, вот гайд по установке: [LINK](https://docs.docker.com/engine/install/)

2. Вот комманды, которые могут понадобиться:

Предполагается, что ваш current_path - папка проекта. Будьте аккуратны с местом запуска, если не уверены, уточните путь до docker-compose.yml через опцию -f.

- Сборка всех контейнеров и их образов: `docker compose build`
- Запуск контейнеров: `docker compose up -d`
- Вход в контейнер: `docker exec -it scooters-order-offer-service-1 /bin/bash`
- Остановка контейнеров: `docker compose down`
- Уборка образов (прогоните, как закончим с проектом, чтобы не забивать место на диске) : `docker compose down --rmi`

3. Потенциальные проблемы:
- Хорошо бы проверить, что локально у вас не запущены старые процессы/контейнеры с такими же названиями. Комманды: `systemctl list-units` и `docker ps`
- Если у вас включен vpn, у docker'а могут возникнуть проблемы с выделением портов.
