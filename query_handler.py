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
# Глобальная переменная для хранения истории пользователей
user_histories = {}
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

# Инициализация списка для хранения диалога и переменной для отслеживания времени
dialog_history = []
MAX_MESSAGES = 5  # Максимальное количество сообщений в диалоге
TIME_LIMIT = 3600  # Время хранения данных в секундах (1 час)

def add_message_to_history(user_id, question, answer):
    current_time = time.time()
    
    # Инициализация истории для нового пользователя
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # Удаление устаревших сообщений
    user_histories[user_id] = [msg for msg in user_histories[user_id] if current_time - msg['timestamp'] < TIME_LIMIT]
    
    # Добавление нового сообщения в историю
    user_histories[user_id].append({'timestamp': current_time, 'question': question, 'answer': answer})

def get_most_relevant_document(query):
    min_distance = float('inf')
    most_relevant_doc = None

    for filename, vs in vector_stores.items():
        docs = vs.similarity_search_with_score(query, k=1)
        if docs:
            distance = docs[0][1]
            if distance < min_distance:
                min_distance = distance
                most_relevant_doc = filename

    return most_relevant_doc

def get_context(user_id, query):
    relevant_doc = get_most_relevant_document(query)
    
    if relevant_doc:
        docs = vector_stores[relevant_doc].similarity_search(query, k=5)
        context = "\n\n".join([d.page_content for d in docs])
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
        # Формируем историю пользователя для контекста
        dialog_context = "\n".join([f"Вопрос: {msg['question']}\nОтвет: {msg['answer']}" for msg in user_histories.get(user_id, [])])
        
        # Добавляем историю пользователя в контекст
        prompt_input = {
            "context": f"Используй контекст:\n{dialog_context}\n\n{context_info['context']}",
            "question": query
        }
        
        response = chain.invoke(prompt_input)
        
        # Сохраняем вопрос и ответ в истории пользователя
        add_message_to_history(user_id, query, response)
        
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