import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),  # Логирование в файл
        logging.StreamHandler()            # Логирование в консоль
    ]
)

# Отключаем логирование для библиотеки telegram
logging.getLogger('telegram').setLevel(logging.WARNING)

def log_start():
    logging.info("Бот начал свою работу.")

def log_periodic():
    logging.info("Бот стабильно продолжает работу.")

def log_received_question(user_info, user_message):
    first_name, last_name, username = user_info
    logging.info(f"Получено сообщение от пользователя {username} ({first_name} {last_name}): {user_message}")

def log_relevant_chunks(chunks):
    for chunk in chunks:
        logging.info(f"Релевантный чанк: {chunk}")

def log_selected_document(document):
    logging.info(f"Выбранный документ: {document}")

def log_ai_response(response):
    logging.info(f"Ответ ИИ: {response}")