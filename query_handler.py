import os
import time
import re
from unidecode import unidecode
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from yandex_chain import YandexLLM, YandexEmbeddings
from logger import log_relevant_documents, log_relevant_chunks

# Путь к директории с векторными базами данных
vector_store_path = "VDB"

# Инициализация объекта embeddings
embeddings = YandexEmbeddings(folder_id="b1gl2okl62ftk25l20uh", api_key="AQVNwlhgV0_s6XQwJv_XYP3cY-LM8w50dsCSQi-H")

# Функция для загрузки векторных баз данных
def load_vector_stores():
    vector_stores = {}
    for file in os.listdir(vector_store_path):
        if file.endswith("_vector_store"):
            vector_stores[file] = FAISS.load_local(
                os.path.join(vector_store_path, file),
                embeddings,
                allow_dangerous_deserialization=True  # Разрешаем опасную десериализацию
            )
    return vector_stores

# Загрузка векторных баз данных
vector_stores = load_vector_stores()

# Инициализация LLM
LLM = YandexLLM(folder_id="b1gl2okl62ftk25l20uh", api_key="AQVNwlhgV0_s6XQwJv_XYP3cY-LM8w50dsCSQi-H", temperature=0.2)

template = """
Ты - юридический ассистент.
Используй только предоставленную информацию для ответа на вопрос. Не добавляй никакой информации от себя.

{context}

Вопрос: {question}
Постарайся ответить максимально правильно. 
Помни, что за ложный ответ предусмотрен штраф -1 балл к рейтингу.
"""
prompt = ChatPromptTemplate.from_template(template)

# Создание цепочки
chain = (
    prompt
    | LLM
    | StrOutputParser()
)

def get_most_relevant_document(query):
    min_distance = float('inf')
    most_relevant_doc = None

    documents_used = []  # Для хранения использованных документов

    for filename, vs in vector_stores.items():
        docs = vs.similarity_search_with_score(query, k=1)
        if docs:
            distance = docs[0][1]
            documents_used.append((filename, distance))  # Добавляем документ и его расстояние
            
            if distance < min_distance:
                min_distance = distance
                most_relevant_doc = filename

    # Логируем использованные документы по убыванию релевантности (по расстоянию)
    documents_used.sort(key=lambda x: x[1])  # Сортируем по расстоянию (меньшее значение — более релевантно)
    
    # Записываем только топ-5 документов в логах (если есть)
    top_documents = [doc[0] for doc in documents_used[:5]]
    
    log_relevant_documents(top_documents)

    return most_relevant_doc

def get_context(user_id, query):
    relevant_doc = get_most_relevant_document(query)
    
    if relevant_doc:
        docs = vector_stores[relevant_doc].similarity_search(query, k=5)
        
        context_chunks = [d.page_content for d in docs]
        
        # Логируем выбранные чанки контекста 
        #log_relevant_chunks(context_chunks)

        context = "\n\n".join(context_chunks)
        
        return {
            "context": context,
            "document": relevant_doc,
            "success": True
        }
    
    return {
        "context": "Не удалось найти релевантный документ.",
        "document": None,
        "success": False
    }

def process_query(user_id, query):
    context_info = get_context(user_id, query)
    
    if context_info["success"]:
       prompt_input = {
           "context": context_info['context'],  
           "question": query
       }
       
       response = chain.invoke(prompt_input)
       return {
           "answer": response,
           "document": context_info["document"],
           "context": context_info["context"]
       }
    
    else:
       return {
           "answer": "Извините, не удалось найти информацию для ответа на ваш вопрос.",
           "document": None,
           "context": None
       }