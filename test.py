import requests
import json
import urllib3

# Отключение предупреждений об SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL для отправки запроса
url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Токен, полученный от API
access_token = "eyJjdHkiOiJqd3QiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUlNBLU9BRVAtMjU2In0.fdwQL0-AETtI_CIlOdGfus9tQWf6FIIRdvYjFTOhuOqHjmnWm1Z3c_hm7SybHY6YqjZ4IUAcx8xlzjLXJfASroQ3Ez0tsdYst3zKYyCghJRESXi6scjgaZ7LNRNz6qFe_kgu-8LXG53CpqqMEaVsClDCCHWfVg8CIBmqt35ZiVJ9XuELiDAYbgJe-oj2XymKAfO5Fq_Ef5hsXgYsZhtp3aWoalwfmOBBlWBzoqY73fLcoxKEJN3rmJo8isnYNfgQs52RRJOHCSTmuCoLNiD-iXNjfmjXZCclwEyCIYXGnL0NMi572BE0ny7dAlzWHDuKc1gj9zj_aawdY4E09ME2mA.KF0LPLuOFXx_jK58lrGsKA.ojCFAwtS6QPinOir-7NBbqFg6BgHRJ3nySnwo5k2lIAdgoLx0HTFNBF2E41Vh_v2rWDGGdKim2a5S6_G3qq9Zatxz_DF2srjPvxslQ1Ww28Hxku5mddtCDSPALPnKj4byLPRV5dNWVmOXrDZ2wuvIo9pgmtDbRImaGD3SPR17AEFPn_GYNBpG8YAah1HGHQhMMgfYxbQq8FlXC5o0ZY0rlIHoDZi8Xj_DBZs7dKN_X14zycvNyJSPzymMrZK-aT6qtVPabtoIcFhRGa2KWLjLHMvsBaiducB2OLxiWZSxoqz28pmMWmFxWUZPAFiLrbf4vPlQIYKGcx3b_g3kk0l8kWDvslDeftWOecoYW9pORTX-vMRm-rulgvNZMdLiMZHDcfOVPUBSnYEJdxZcSIQnNPuRJHP1emdlV7RDS2Z83Wwaevl0sbLhwqybf2MbMDgbjcgyIjd6S4zw_SUZ4VPUf1UDzD32Zg8ZvSpl12R-kVRyxA5YDQ3nlony2Z56X6SyJGcd67nYI2KpirVqUHWUY2XyGhEK53C33Hv2eTZowTHwFPF1ZmGhv8hJXnrdnrI73b4ARF82ToFnSxoRIHBk84i88j8XoUgdF_sdk1-EDjJBEd9gZe3EYTzB3QZ6b72-bshrNdWYzZjPjTjalNPvPW8yR6fndxl0zqp47phYVvXjPOiBcdj58VyurLx22JJ42JGaZE6vRqjEYvHWuUdGWEgAlyFKBxWeWOxTv-KbaA.1k4BgAJ-Ikg1lkF2AQdBPVN_naevllQtublD7WshMLg"  # Подставьте полный токен

# Тело запроса
payload = {
    "model": "GigaChat",
    "messages": [
        {
            "role": "user",
            "content": "Привет! Как дела?"
        }
    ],
    "stream": False
}

# Заголовки запроса
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Отправка POST-запроса
try:
    response = requests.post(url, headers=headers, json=payload, verify=False)

    # Проверка успешности запроса
    if response.status_code == 200:
        print("Успешное подключение!")
        print("Ответ от GigaChat:", response.json())
    else:
        print(f"Ошибка! Код ответа: {response.status_code}")
        print("Тело ответа:", response.text)
except Exception as e:
    print(f"Ошибка при подключении: {e}")
