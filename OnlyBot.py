import os
from telegram import Update
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters
from query_handler import process_query
from db_handler import insert_message, check_email_exists, add_email  # Импортируем новые функции
import threading
import time
import re  # Для проверки валидности email
from logger import log_start, log_periodic, log_received_question, log_relevant_chunks, log_selected_document, log_ai_response

# Глобальные переменные для отслеживания состояния ожидания вопросов и регистрации
waiting_for_questions = {}
last_question_times = {}
waiting_for_email = {}  # Словарь для хранения состояния ожидания email

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if not check_email_exists(user_id):
        waiting_for_email[user_id] = True
        await update.message.reply_text("Для продолжения работы введите вашу рабочую почту (должна оканчиваться на @gazprom-neft.ru).")
        return

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
    
    if user_id in waiting_for_email:
        email = update.message.text.strip()
        
        if is_valid_email(email):
            add_email(user_id, update.message.from_user.username or "", email)  # Добавляем email в БД
            del waiting_for_email[user_id]  # Убираем пользователя из ожидания email
            
            await update.message.reply_text("Спасибо! Теперь вы можете задавать вопросы.")
            return
        else:
            await update.message.reply_text("Неверный формат email. Убедитесь, что он заканчивается на @gazprom-neft.ru.")
            return

    if waiting_for_questions.get(user_id, False):
        first_name = update.message.from_user.first_name
        last_name = update.message.from_user.last_name or ""
        username = update.message.from_user.username or ""
        user_message = update.message.text  

        last_question_times[user_id] = time.time()
        
        await update.message.reply_text("Ищу информацию по вашему вопросу!")
        
        log_received_question((first_name, last_name, username), user_message)

        result = process_query(user_id, user_message)
        
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
               document=selected_document)

        log_ai_response(result["answer"])
        
        await update.message.reply_text(result["answer"])
    else:
        await update.message.reply_text("Введите /question чтобы задать вопрос.")

async def question(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if user_id in waiting_for_email:
        await update.message.reply_text("Сначала введите вашу рабочую почту.")
        return

    waiting_for_questions[user_id] = True
    last_question_times[user_id] = time.time()
    await update.message.reply_text("Слушаю ваш вопрос!")

async def stop(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    waiting_for_questions[user_id] = False
    last_question_times.pop(user_id, None)
    
    await update.message.reply_text("Перестал ожидать вопрос. Если хотите задать новый, напишите /question.")

async def info(update: Update, context: CallbackContext) -> None:
    document_list = (
        "<b>Список документов:</b>\n\n"
        "<i>1.</i> <b>Пложение о Закупках;</b>\n"
        "<i>2.</i> <b>Разработка стратегии закупки.</b> <i>Версия: 1.0;</i>\n"
        "<i>3.</i> <b>Требования к порядку рассмотрения, оценки и сопоставления;</b>\n"
        "<i>4.</i> <b>Работа с коммерческими предложениями.</b> <i>Версия: 1.0;</i>\n"
        "<i>5.</i> <b>Проведение Предквалификации потенциальных участников;</b>\n"
        "<i>6.</i> <b>Управление стратегиями закупок.</b> <i>Версия: 1.1;</i>\n"
        "<i>7.</i> <b>Управление эффективностью деятельности контрагента;</b>\n"
        "<i>8.</i> <b>Формирование Годового плана закупок.</b> <i>Версия: 3.1;</i>\n"
        "<i>9.</i> <b>Проведение конкурентного отбора.</b> <i>Версия: 3.0;</i>\n"
        "<i>10.</i> <b>Проведение закупки у единственного поставщика подрядчика;</b>\n"
        "<i>11.</i> <b>Проведение безальтернативной закупки.</b> <i>Версия: 2.1;</i>\n"
        "<i>12.</i> <b>Проведение закупок способом маркетинговые исследования;</b>\n"
        "<i>13.</i> <b>Формирование и рассмотрение заявок на закупку импортных;</b>\n"
        "<i>14.</i> <b>Управление исполнением договорных обязательств.</b>"
    )
    
    await update.message.reply_text(document_list, parse_mode='HTML')

def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@gazprom-neft\.ru$", email) is not None

def periodic_check():
    while True:
        current_time = time.time()
        for user_id in list(waiting_for_questions.keys()):
            if current_time - last_question_times.get(user_id, 0) > 600:
                waiting_for_questions[user_id] = False
                last_question_times.pop(user_id, None)
                logging.info(f"Время ожидания истекло для пользователя {user_id}.")
      
        time.sleep(600)

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