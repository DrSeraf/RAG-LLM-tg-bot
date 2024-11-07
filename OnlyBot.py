# Из нулевого + старое
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader,UnstructuredWordDocumentLoader
import requests
from yandex_chain import YandexLLM
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain.vectorstores import FAISS
from langchain.schema import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import time
from langchain.embeddings.base import Embeddings
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.chains.conversation.memory import ConversationSummaryMemory
# Из 1 фрагмента
import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from yandex_chain import YandexEmbeddings, YandexLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import StrOutputParser
# Из 5 фрагмента
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain.prompts import ChatPromptTemplate
# Недавнее
import re
from unidecode import unidecode
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

# Импортируем функцию для обработки запросов
from query_handler import process_query

#Оформаление текста
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

#Импорт в БД
from db_handler import insert_message


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

def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""
    username = update.message.from_user.username or ""
    user_message = update.message.text  
    
    result = process_query(user_message)
    
    # Вставляем данные в базу данных
    insert_message(user_id=user_id,
                   fio=f"{first_name} {last_name}",
                   username=username,
                   user_message=user_message,
                   bot_response=result["answer"])

    # Отправляем ответ пользователю
    update.message.reply_text(result["answer"])

def main():
    # Замените 'YOUR_TOKEN' на токен вашего бота
    updater = Updater("YOUR_TOKEN")
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    
    updater.idle()

if __name__ == '__main__':
    main()