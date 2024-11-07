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

loader_pdf = DirectoryLoader("НМД", glob="**/*.pdf", loader_cls=PyPDFLoader)
docs_pdf = loader_pdf.load()

#import re
#from unidecode import unidecode
#import os

import os

# Путь к директории с документами
directory_path = "НМД"
# Путь к директории для сохранения векторных баз
vector_store_path = "VDB"

# Создание директории VDB, если она не существует
if not os.path.exists(vector_store_path):
    os.makedirs(vector_store_path)

def clean_text(text):
    # Удаление символов новой строки
    text = text.replace("\n", "")

    # Замена двойных пробелов на один
    text = text.replace("  ", " ")

    # Замена неразрывного пробела на обычный перевод строки
    text = text.replace("\xa0", "\n")

    # Замена табуляции на один пробел
    text = text.replace("\t", " ")

    # Удаление специальных символов, кроме русских букв и пробелов
    text = re.sub(r'[^\w\s\-.,;!?А-Яа-яЁё]', ' ', text)

    # Замена множественных пробелов на один
    text = re.sub(r'\s+', ' ', text)

    # Удаление начальных и конечных пробелов
    text = text.strip()

    # Удаление номеров страниц (предполагая, что они находятся в конце строки)
    text = re.sub(r'\s+\d+\s*$', '', text)

    return text

# Создание словаря для группировки документов по имени файла
file_groups = {}
for doc in docs_pdf:
    # Извлечение имени файла без расширения
    filename = os.path.splitext(os.path.basename(doc.metadata['source']))[0]
    if filename not in file_groups:
        file_groups[filename] = []
    file_groups[filename].append(doc)

# Обработка каждой группы документов
for filename, group in file_groups.items():
    for doc in group:
        # Применение функции очистки к содержимому страницы
        doc.page_content = clean_text(doc.page_content)

        # Дополнительная обработка для удаления возможных артефактов PDF
        lines = doc.page_content.split('\n')
        # Удаление коротких строк (менее 5 символов)
        cleaned_lines = [line for line in lines if len(line.strip()) > 5]
        # Объединение очищенных строк обратно в текст
        doc.page_content = ' '.join(cleaned_lines)

#from langchain.text_splitter import RecursiveCharacterTextSplitter

# Функция для подсчета общего количества чанков
def count_total_chunks(chunks_list):
    return sum(len(chunks) for chunks in chunks_list)

# Можно менять все параметры
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
)

# Список для хранения чанков каждого документа
all_chunks = []

for filename, group in file_groups.items():
    for doc in group:
        chunks = splitter.split_text(doc.page_content)
        all_chunks.append(chunks)
        print(f"Документ '{filename}' разделен на {len(chunks)} чанков.")

# Подсчет общего количества чанков
total_chunks = count_total_chunks(all_chunks)
print(f"\nОбщее количество чанков: {total_chunks}")

# Если нужно, можно вывести дополнительную статистику
print(f"Количество обработанных документов: {len(file_groups)}")
print(f"Среднее количество чанков на документ: {total_chunks / len(file_groups):.2f}")

embeddings = YandexEmbeddings(folder_id="b1gl2okl62ftk25l20uh", api_key="AQVNwlhgV0_s6XQwJv_XYP3cY-LM8w50dsCSQi-H")

vector_stores = {}
for filename, group in file_groups.items():
    split_docs = splitter.split_documents(group)
    vector_stores[filename] = FAISS.from_documents(split_docs, embeddings)

    # Сохранение векторного хранилища в папку VDB
    vector_stores[filename].save_local(os.path.join(vector_store_path, f"{filename}_vector_store"))  # Исправлено на save_local()

print(f"Векторные базы данных сохранены в директории '{vector_store_path}'.")
