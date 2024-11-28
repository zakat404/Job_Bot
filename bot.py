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
from pdfminer.high_level import extract_text
from hh_analyzer import fetch_vacancies

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


def process_resume(text):
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
            assistant_message = gigachat_response["choices"][0]["message"]["content"]
            return json.loads(assistant_message)
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f"Ошибка извлечения или парсинга данных из ответа GigaChat: {e}")
            return None
    return None


def map_experience(experience):
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


async def handle_pdf(update: Update, context):
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    file_path = os.path.join("resumes", file_name)
    os.makedirs("resumes", exist_ok=True)
    await file.download_to_drive(file_path)
    await update.message.reply_text("Резюме получено. Обрабатываю данные...")

    try:
        text = extract_text(file_path)
        if not text.strip():
            await update.message.reply_text(
                "Не удалось извлечь текст из PDF. Убедитесь, что документ содержит текст, а не только изображения."
            )
            return
    except Exception as e:
        logging.error(f"Ошибка извлечения текста из PDF: {e}")
        await update.message.reply_text("Ошибка при обработке PDF файла.")
        return

    result = process_resume(text)

    if result:
        session = Session()
        try:
            new_resume = Resume(**result)
            session.add(new_resume)
            session.commit()

            await update.message.reply_text("Данные успешно сохранены в базу.")

            skills = result.get("skills", "Python")
            location = result.get("location", "Санкт-Петербург")
            experience = result.get("experience", "0")
            specialty = result.get("specialty", "Разработчик")

            vacancies = fetch_vacancies(skills, location, experience, specialty)

            if vacancies:
                response_message = "Подходящие вакансии:\n"
                for vacancy in vacancies:
                    response_message += f"- [{vacancy['name']}]({vacancy['alternate_url']})\n"
                await update.message.reply_text(response_message, parse_mode="Markdown")
            else:
                await update.message.reply_text("К сожалению, подходящих вакансий не найдено.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении в базу данных: {e}")
            await update.message.reply_text("Ошибка при сохранении данных в базу.")
        finally:
            session.close()
    else:
        await update.message.reply_text("Ошибка при обработке резюме.")


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    application.run_polling()


if __name__ == "__main__":
    main()
