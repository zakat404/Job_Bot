import requests
import logging

HH_API_URL = "https://api.hh.ru/vacancies"


def get_area_id(city_name):
# Получить идентификатор региона по названию города
    try:
        response = requests.get("https://api.hh.ru/areas")
        if response.status_code == 200:
            areas = response.json()
            for country in areas:  # Перебор стран
                for area in country.get("areas", []):  # Перебор регионов
                    if area["name"].lower() == city_name.lower():
                        return area["id"]
                    for sub_area in area.get("areas", []):  # Перебор подрегионов
                        if sub_area["name"].lower() == city_name.lower():
                            return sub_area["id"]
            return None
        else:
            logging.error(f"Ошибка при запросе списка регионов: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении area_id: {e}")
        return None

def fetch_vacancies(skills, location, experience, specialty=None):
    area_id = get_area_id(location)
    if not area_id:
        logging.error(f"Не удалось определить ID региона для локации: {location}")
        return None

    experience_mapped = map_experience(experience)

# Разбиваем навыки
    skills_list = [s.strip() for s in skills.split(',')]
    top_skills = ' '.join(skills_list[:3])

# Формируем упрощённый поисковый запрос
    if specialty:
        search_text = f"{specialty} {top_skills}"
    else:
        search_text = top_skills

    logging.info(f"Поиск вакансий с текстом: {search_text}, регион ID: {area_id}, опыт: {experience_mapped}")

    params = {
        "text": search_text,
        "area": area_id,
        "experience": experience_mapped,
        "per_page": 5,
    }

    try:
        response = requests.get(HH_API_URL, params=params, headers={"User-Agent": "TelegramBot"})
        if response.status_code == 200:
            vacancies = response.json()["items"]
            if not vacancies:
                logging.info(f"Вакансии не найдены по запросу: {params}")
            return vacancies
        else:
            logging.error(f"Ошибка API hh.ru. Код ответа: {response.status_code}")
            logging.error(f"Тело ответа: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при запросе к HH.ru: {e}")
        return None

def map_experience(experience):
# Сопоставляет опыт работы с форматами API hh.ru.
    experience_str = str(experience).lower()

    if "без опыта" in experience_str or "0" in experience_str:
        return "noExperience"
    elif "1" in experience_str or "2 года" in experience_str:
        return "between1And3"
    elif "3" in experience_str or "4" in experience_str or "5" in experience_str:
        return "between3And6"
    elif "6" in experience_str or "более" in experience_str:
        return "moreThan6"
    else:
        return "noExperience"