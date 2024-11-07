import os
from telegram import Update
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
# Импортируем функцию для обработки запросов
from query_handler import process_query
# Импорт в БД
from db_handler import insert_message
import threading
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),  # Логирование в файл
        logging.StreamHandler()            # Логирование в консоль
    ]
)

def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "<b>Добрый день, Коллега!</b>\n\n"
        "Я здесь, чтобы помочь вам с различными задачами.\n"
        "Вот некоторые команды, которые вы можете использовать:\n"
        "• <i>/start</i> - начать диалог со мной\n"
        #"• <i>/info</i> - узнать больше о боте\n"
        #"• <i>/contact</i> - связаться с поддержкой\n\n"
        "Задавайте вопросы по НМД, я всегда рад ответить вам на них!"
    )
    
    update.message.reply_text(welcome_message, parse_mode='HTML')
    logging.info("Бот начал работу.")

def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""
    username = update.message.from_user.username or ""
    user_message = update.message.text  
    
    logging.info(f"Получен вопрос от {first_name} {last_name} (@{username}): {user_message}")

    result = process_query(user_message)
    
    # Вставляем данные в базу данных
    insert_message(user_id=user_id,
                   fio=f"{first_name} {last_name}",
                   username=username,
                   user_message=user_message,
                   bot_response=result["answer"])

    # Отправляем ответ пользователю
    update.message.reply_text(result["answer"])

def periodic_logging():
    while True:
        logging.info("Бот стабильно продолжает работу.")
        time.sleep(3600)  # Логировать каждый час

def main():
    # Замените 'YOUR_TOKEN' на токен вашего бота
    updater = Updater("7902299353:AAEr8S8lybuzGM1A4OmBtUdr-n4ItPs9tBs")
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
# Запуск потока для периодического логирования
    threading.Thread(target=periodic_logging, daemon=True).start()

    updater.start_polling()
    
    updater.idle()

if __name__ == '__main__':
    main()
