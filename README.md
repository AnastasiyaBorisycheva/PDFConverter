1. Установить docker-compose на сервер:
    Выполнить поочередно

        sudo apt update
        sudo apt install curl
        curl -fSL https://get.docker.com -o get-docker.sh
        sudo sh ./get-docker.sh
        sudo apt install docker-compose-plugin


2. Создать на сервере папку pdfconverter

3. В папке pdfconverter создать файл docker-compose.production.yml
    В файл поместить следующее содержимое:

    ```
        version: '3'

        services:
        converter:
            image: anastasiiaborisycheva/pdfconverter
            env_file: .env

    ```

4. В папке pdfconverter создать файл .env
        Поместить в него переменную BOT_TOKEN
        Значение взять у меня в личке

5. Стартовать бота следующей командой

    sudo docker compose -f docker-compose.production.yml up -d