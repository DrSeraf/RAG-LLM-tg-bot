import logging

# Настройка основного логирования
app_logger = logging.getLogger("my_bot_logger")
app_logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования на INFO

# Создание обработчиков
file_handler = logging.FileHandler("bot_log.txt")
stream_handler = logging.StreamHandler()

# Настройка формата
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Добавление обработчиков к логгеру
app_logger.addHandler(file_handler)
app_logger.addHandler(stream_handler)

def log_start():
    app_logger.info("Бот начал свою работу.")

def log_periodic():
    app_logger.info("Бот стабильно продолжает работу.")

def log_user_question(user_id, username, user_message):
    app_logger.info(f"Пользователь {user_id} ({username}) задал вопрос: \"{user_message}\"")

def log_relevant_documents(documents):
    app_logger.info("Список документов:")
    for i, doc in enumerate(documents, start=1):
        app_logger.info(f"{i}) {doc}")

def log_relevant_chunks(chunks):
    app_logger.info("Список чанков:")
    for i, chunk in enumerate(chunks, start=1):
        app_logger.info(f"{i}) \"{chunk}\"")

def log_prompt(prompt):
    app_logger.info(f"Промт боту: \"{prompt}\"")

def log_ai_response(response):
    app_logger.info(f"Ответ бота: \"{response}\"")

def log_received_question(user_info, user_message):
    first_name, last_name, username = user_info
    app_logger.info(f"Получено сообщение от пользователя {username} ({first_name} {last_name}): {user_message}")

def log_relevant_chunks_with_distance(chunks_info):
    app_logger.info("Список чанков:")
    for distance, doc_name, chunk in chunks_info:
        app_logger.info(f"{distance:.4f} - {doc_name}: \"{chunk}\"")  # Форматируем расстояние до 4 знаков после запятой