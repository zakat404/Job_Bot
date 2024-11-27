import requests
import logging

# URL API hh.ru
HH_API_URL = "https://api.hh.ru/vacancies"


def fetch_vacancies(skills, location, experience):
    """
    Функция для получения списка вакансий с hh.ru
    :param skills: Список навыков кандидата (через запятую)
    :param location: Город проживания кандидата
    :param experience: Опыт работы в годах
    :return: Список вакансий или None
    """
    headers = {
        "User-Agent": "MyBot/1.0 (https://mybot.example.com)"
    }

    # Параметры запроса
    params = {
        "text": skills,  # Используем навыки кандидата как ключевые слова
        "area": location,  # Локация кандидата (ID региона, см. документацию hh.ru)
        "experience": map_experience_to_hh(experience),  # Преобразование опыта
        "per_page": 5  # Количество вакансий
    }

    try:
        response = requests.get(HH_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])  # Возвращаем список вакансий
        else:
            logging.error(f"Ошибка API hh.ru. Код ответа: {response.status_code}")
            logging.error(f"Тело ответа: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при запросе к API hh.ru: {e}")
        return None


def map_experience_to_hh(experience):
    """
    Преобразует опыт работы в формат hh.ru:
    - 1: без опыта
    - 2: от 1 до 3 лет
    - 3: от 3 до 6 лет
    - 4: более 6 лет
    """
    if experience < 1:
        return "noExperience"
    elif 1 <= experience <= 3:
        return "between1And3"
    elif 3 < experience <= 6:
        return "between3And6"
    else:
        return "moreThan6"


# Пример вызова функции
if __name__ == "__main__":
    skills = "Python, Django, Flask"
    location = "1"  # ID Москвы
    experience = 2  # 2 года опыта

    vacancies = fetch_vacancies(skills, location, experience)

    if vacancies:
        for vacancy in vacancies:
            print(f"Название: {vacancy['name']}")
            print(f"Ссылка: {vacancy['alternate_url']}")
            print(f"Работодатель: {vacancy.get('employer', {}).get('name', 'Не указан')}")
            print(f"Зарплата: {vacancy.get('salary', {}).get('from', 'Не указана')}")
            print("-" * 40)
    else:
        print("Не удалось получить вакансии.")
