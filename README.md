# ЗАПУСК
### Сборка образа
```bash
docker build -t glossary_app .
```
### Запуск контейнера
```bash
docker run -d --name mycontainer -p 80:80 glossary_app
```
### После запуска контейнера документация будет доступна по адресу
http://127.0.0.1/docs

