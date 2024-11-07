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

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я юридический ассистент. Задайте мне вопрос.')

def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text  
    result = process_query(user_message)
    update.message.reply_text(result["answer"])

def main():
    # Замените 'YOUR_TOKEN' на токен вашего бота
    updater = Updater("7902299353:AAEr8S8lybuzGM1A4OmBtUdr-n4ItPs9tBs")
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    
    updater.idle()

if __name__ == '__main__':
    main()