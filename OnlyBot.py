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
waiting_for_questions = {}  # Словарь для хранения состояния ожидания для каждого пользователя
last_question_times = {}  # Словарь для хранения времени последнего запроса для каждого пользователя

async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "<b>Добрый день, Коллега!</b>\n\n"
        "Я здесь, чтобы помочь вам с различными задачами.\n"
        "Вот некоторые команды, которые вы можете использовать:\n"
        "• <i>/start</i> - начать диалог со мной\n"
        "• <i>/question</i> - задать вопрос\n"
        "• <i>/stop</i> - остановить ожидание вопроса\n"
        "• <i>/info</i> - получить список документов\n"
        "Задавайте вопросы по НМД, я всегда рад ответить вам на них!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='HTML')
    log_start()

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if waiting_for_questions.get(user_id, False):
        first_name = update.message.from_user.first_name
        last_name = update.message.from_user.last_name or ""
        username = update.message.from_user.username or ""
        user_message = update.message.text  

        last_question_times[user_id] = time.time()  # Обновляем время последнего запроса
        
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
               bot_response=result["answer"],
               document=selected_document) #Добавляем документ выбранный

        log_ai_response(result["answer"])
        
        await update.message.reply_text(result["answer"])
    else:
        await update.message.reply_text("Введите /question чтобы задать вопрос.")

async def question(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    waiting_for_questions[user_id] = True
    last_question_times[user_id] = time.time()  # Сохраняем текущее время
    await update.message.reply_text("Слушаю ваш вопрос!")

async def stop(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    waiting_for_questions[user_id] = False
    last_question_times.pop(user_id, None)  # Удаляем время последнего запроса
    await update.message.reply_text("Перестал ожидать вопрос. Если хотите задать новый, напишите /question.")

async def info(update: Update, context: CallbackContext) -> None:
    document_list = (
        "<b>Список документов:</b>\n"
        "1) ПоЗ\n"
        "2) М 03 01 03 01 Разработка стратегии закупки версия 1 0\n"
        "3) М 03 03 01 01 01 Требования к порядку рассмотрения, оценки и сопоставления\n"
        "4) М 03 05 02 02 Работа с коммерческими предложениями версия 1 0\n"
        "5) СК 03 01 02 Проведение Предквалификации потенциальных участников\n"
        "6) СК 03 01 03 Управление стратегиями закупок версия 1 1\n"
        "7) СК 03 01 05 01 Управление эффективностью деятельности контрагента\n"
        "8) СК 03 02 01 Формирование Годового плана закупок версия 3 1\n"
        "9) СК 03 03 01 01 Проведение конкурентного отбора версия 3 0\n"
        "10) СК 03 03 02 01 Проведение закупки у единственного поставщика подрядчика\n"
        "11) СК 03 03 02 02 Проведение безальтернативной закупки версия 2 1\n"
        "12) СК 03 03 02 03 Проведение закупок способом маркетинговые исследования\n"
        "13) СК 03 05 02 Формирование и рассмотрение заявок на закупку импортных\n"
        "14) СК 03 07 01 02 Управление исполнением договорных обязательств"
    )
    
    await update.message.reply_text(document_list, parse_mode='HTML')
    
    await update.message.reply_text(document_list, parse_mode='HTML')

def periodic_check():
    while True:
        current_time = time.time()
        for user_id in list(waiting_for_questions.keys()):
            if current_time - last_question_times.get(user_id, 0) > 600:  # 10 минут
                waiting_for_questions[user_id] = False
                last_question_times.pop(user_id, None)  # Удаляем время последнего запроса
                logging.info(f"Время ожидания истекло для пользователя {user_id}.")
      
        time.sleep(600)  # Проверяем каждую минуту

def main():
    application = ApplicationBuilder().token("7902299353:AAEr8S8lybuzGM1A4OmBtUdr-n4ItPs9tBs").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("question", question))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    threading.Thread(target=periodic_check, daemon=True).start()

    application.run_polling()
    
if __name__ == '__main__':
    main()