import os
import logging
import json
import requests
import urllib3
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from hh_analyzer import analyze_and_fetch_vacancies


# Отключение предупреждений об SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Загрузка переменных окружения из .env
load_dotenv()

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# URL для GigaChat
GIGACHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Настройка базы данных
engine = create_engine(DATABASE_URL)
Base = declarative_base()


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    skills = Column(Text)
    specialty = Column(String)
    experience = Column(String)
    location = Column(String)
    social_links = Column(Text)
    salary = Column(String)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# Функция для отправки запроса в GigaChat
def send_to_gigachat(content):
    headers = {
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": content}],
        "stream": False
    }

    try:
        response = requests.post(GIGACHAT_URL, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Ошибка! Код ответа: {response.status_code}")
            logging.error(f"Тело ответа: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при подключении к GigaChat: {e}")
        return None


# Функция для подготовки промпта и обработки ответа
def process_resume(text):
    # Изменяем промпт для получения данных в JSON формате
    prompt = (
        "Извлеките следующую информацию из текста резюме и верните её в формате JSON:\n"
        "{\n"
        "  \"name\": \"Имя и фамилия\",\n"
        "  \"phone\": \"Номер телефона\",\n"
        "  \"email\": \"Электронная почта\",\n"
        "  \"skills\": \"Список навыков (через запятую)\",\n"
        "  \"specialty\": \"Желаемая должность\",\n"
        "  \"experience\": \"Общий опыт работы (в годах)\",\n"
        "  \"location\": \"Город проживания\",\n"
        "  \"social_links\": \"Ссылки на соцсети или портфолио (через запятую)\",\n"
        "  \"salary\": \"Желаемая зарплата\"\n"
        "}\n"
        f"Текст резюме: {text}"
    )
    gigachat_response = send_to_gigachat(prompt)

    if gigachat_response:
        try:
            # Попробуем получить JSON-ответ из GigaChat
            assistant_message = gigachat_response["choices"][0]["message"]["content"]
            data = json.loads(assistant_message)  # Парсим JSON-ответ
            return data
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f"Ошибка извлечения или парсинга данных из ответа GigaChat: {e}")
            logging.error(f"Ответ от GigaChat: {gigachat_response}")
            return None
    return None

from pdfminer.high_level import extract_text

# Функция для парсинга ответа GigaChat
def parse_gigachat_response(response_text):
    data = {}
    lines = response_text.split("\n")
    for line in lines:
        if "Имя:" in line:
            data["name"] = line.split("Имя:")[1].strip()
        elif "Телефон:" in line:
            data["phone"] = line.split("Телефон:")[1].strip()
        elif "Email:" in line:
            data["email"] = line.split("Email:")[1].strip()
        elif "Навыки:" in line:
            # Навыки обрабатываются как список
            skills = line.split("Навыки:")[1].strip()
            data["skills"] = ", ".join([skill.strip() for skill in skills.split(",")])
        elif "Должность:" in line:
            data["specialty"] = line.split("Должность:")[1].strip()
        elif "Опыт работы:" in line:
            data["experience"] = line.split("Опыт работы:")[1].strip()
        elif "Локация:" in line:
            data["location"] = line.split("Локация:")[1].strip()
        elif "Социальные ссылки:" in line:
            # Ссылки обрабатываются как список
            links = line.split("Социальные ссылки:")[1].strip()
            data["social_links"] = ", ".join([link.strip() for link in links.split(",")])
        elif "Зарплата:" in line:
            data["salary"] = line.split("Зарплата:")[1].strip()
    return data


# Обработчик получения PDF файла
from pdfminer.high_level import extract_text

async def handle_pdf(update: Update, context):
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    file_path = os.path.join("resumes", file_name)
    os.makedirs("resumes", exist_ok=True)
    await file.download_to_drive(file_path)
    await update.message.reply_text("Резюме получено. Обрабатываю данные...")

    # Извлечение текста из PDF с использованием pdfminer
    try:
        text = extract_text(file_path)
        if not text.strip():
            await update.message.reply_text("Не удалось извлечь текст из PDF. Убедитесь, что документ содержит текст, а не только изображения.")
            return
    except Exception as e:
        logging.error(f"Ошибка извлечения текста из PDF: {e}")
        await update.message.reply_text("Ошибка при обработке PDF файла. Возможно, файл поврежден.")
        return

    # Обработка текста резюме
    result = process_resume(text)

    if result:
        session = Session()
        try:
            new_resume = Resume(**result)
            session.add(new_resume)
            session.commit()
            await update.message.reply_text("Данные успешно сохранены в базу.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении в базу данных: {e}")
            await update.message.reply_text("Ошибка при сохранении данных в базу.")
        finally:
            session.close()
    else:
        await update.message.reply_text("Ошибка при обработке резюме.")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    analyze_and_fetch_vacancies()

    # Обработчик для приема PDF-файлов
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    application.run_polling()


if __name__ == "__main__":
    main()
