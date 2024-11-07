import os
from telegram import Update
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters
from query_handler import process_query
from db_handler import insert_message
import threading
import time
from logger import log_start, log_periodic, log_received_question, log_relevant_chunks, log_selected_document, log_ai_response

# Глобальные переменные для отслеживания состояния ожидания вопросов
waiting_for_question = False
last_question_time = None

async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "<b>Добрый день, Коллега!</b>\n\n"
        "Я здесь, чтобы помочь вам с различными задачами.\n"
        "Вот некоторые команды, которые вы можете использовать:\n"
        "• <i>/start</i> - начать диалог со мной\n"
        "• <i>/question</i> - задать вопрос\n"
        "• <i>/stop</i> - остановить ожидание вопроса\n"
        "• <i>/info</i> - получить информацию\n"
        "Задавайте вопросы по НМД, я всегда рад ответить вам на них!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='HTML')
    log_start()

async def handle_message(update: Update, context: CallbackContext) -> None:
    global waiting_for_question, last_question_time
    
    if waiting_for_question:
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name
        last_name = update.message.from_user.last_name or ""
        username = update.message.from_user.username or ""
        user_message = update.message.text  

        last_question_time = time.time()  # Обновляем время последнего запроса
        
        await update.message.reply_text("Ищу информацию по вашему вопросу!")
        
        log_received_question((first_name, last_name, username), user_message)

        result = process_query(user_message)
        
        relevant_chunks = result.get("context", "").split("\n\n")
        log_relevant_chunks(relevant_chunks)

        selected_document = result.get("document")
        if selected_document:
            log_selected_document(selected_document)

        insert_message(user_id=user_id,
                       fio=f"{first_name} {last_name}",
                       username=username,
                       user_message=user_message,
                       bot_response=result["answer"])

        log_ai_response(result["answer"])
        
        await update.message.reply_text(result["answer"])
    else:
        await update.message.reply_text("Введите /question чтобы задать вопрос.")

async def question(update: Update, context: CallbackContext) -> None:
    global waiting_for_question, last_question_time
    waiting_for_question = True
    last_question_time = time.time()  # Сохраняем текущее время
    await update.message.reply_text("Слушаю ваш вопрос!")

async def stop(update: Update, context: CallbackContext) -> None:
    global waiting_for_question
    waiting_for_question = False
    await update.message.reply_text("Перестал ожидать вопрос. Если хотите задать новый, напишите /question.")

async def info(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Держи информацию")

def periodic_check():
    global waiting_for_question, last_question_time
    
    while True:
        if waiting_for_question and last_question_time is not None:
            current_time = time.time()
            if current_time - last_question_time > 600:  # 10 минут
                waiting_for_question = False
                last_question_time = None  # Сброс времени
                logging.info("Время ожидания истекло.")
                # Здесь можно добавить код для отправки сообщения пользователю о завершении ожидания.
        
        time.sleep(60)  # Проверяем каждую минуту

def main():
    application = ApplicationBuilder().token("YOUR_TOKEN_HERE").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("question", question))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    threading.Thread(target=periodic_check, daemon=True).start()

    application.run_polling()
    
if __name__ == '__main__':
    main()