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
Учитывай мои вопросы и ответы, которые ты давал, для формирования более точного ответа.

{context}

Вопрос: {question}
Постарайся ответить максимально правильно. ОЧЕНЬ ВАЖНО, ЕСЛИ ТЫ НЕ ЗНАЕШЬ ОТВЕТ - ОТВЕТЬ Я НЕ ЗНАЮ. ЭТО СТРОГАЯ ИНСТРУКЦИЯ. ЗА ЛОЖНЫЙ ОТВЕТ ТЕБЕ ВЫПИШУТ ШТРАФ -1 БАЛЛ К РЕЙТИНГУ.
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

def add_message_to_history(question, answer):
    global dialog_history
    current_time = time.time()
    dialog_history[:] = [msg for msg in dialog_history if current_time - msg['timestamp'] < TIME_LIMIT]
    dialog_history.append({'timestamp': current_time, 'question': question, 'answer': answer})
    if len(dialog_history) > MAX_MESSAGES:
        dialog_history.pop(0)

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

def get_context(query):
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

def process_query(query):
    global dialog_history  
    context_info = get_context(query)
    
    if context_info["success"]:
        dialog_context = "\n".join([f"Вопрос: {msg['question']}\nОтвет: {msg['answer']}" for msg in dialog_history])
        dialog_context += f"\nВопрос: {query}\n"
        
        prompt_input = {
            "context": f"{dialog_context}\n{context_info['context']}",
            "question": query
        }
        
        response = chain.invoke(prompt_input)
        add_message_to_history(query, response)
        
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
