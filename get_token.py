import requests
import base64
import time
from dotenv import set_key, load_dotenv
import os

# Загрузка переменных из .env
dotenv_path = ".env"
load_dotenv(dotenv_path)

# Клиент ID и Секрет
CLIENT_ID = "44a28871-6418-44e1-ae24-1b42cfeaac44"
CLIENT_SECRET = "9fb5a511-5ee3-4387-8b9d-fe95c84664b6"

# URL для получения токена
URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"


def get_access_token():
    # Кодируем Client ID и Client Secret в Base64
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "4e3decf3-dfee-4e62-b76d-3498a83085a6",  # Можно генерировать UUID каждый раз
        "Authorization": f"Basic {auth_bytes}"
    }

    payload = "scope=GIGACHAT_API_PERS"

    try:
        response = requests.post(URL, headers=headers, data=payload, verify=False)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"Получен токен: {access_token}")

            # Сохраняем токен в .env
            set_key(dotenv_path, "GIGACHAT_TOKEN", access_token)
            print("Токен сохранен в .env")
            return access_token
        else:
            print(f"Ошибка получения токена: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Ошибка при запросе токена: {e}")
        return None


# Основная функция
def main():
    while True:
        get_access_token()
        print("Ожидание 30 минут перед обновлением токена...")
        time.sleep(1800)  # 30 минут = 1800 секунд


if __name__ == "__main__":
    main()
