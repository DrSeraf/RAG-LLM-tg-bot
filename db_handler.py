import mysql.connector
from mysql.connector import Error

# Функция для подключения к базе данных
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='217.114.43.104',
            port=3306,
            user='seraf',
            password='ark_wenegreT1',
            database='boriy_bot'
        )
        if connection.is_connected():
            print("Успешное подключение к БД")
            return connection
    except Error as e:
        print(f"Ошибка подключения: {e}")
        return None

# Функция для вставки данных в таблицу messages
def insert_message(user_id, fio, username, user_message, bot_response, document):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = """
        INSERT INTO messages (user_id, fio, username, user_message, bot_response, doc)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (user_id, fio, username, user_message, bot_response, document)
        
        try:
            cursor.execute(query, values)
            connection.commit()
            print("Данные успешно записаны в БД")
        except Error as e:
            print(f"Ошибка при вставке данных: {e}")
        finally:
            cursor.close()
            connection.close()

def check_email_exists(user_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        
        query = "SELECT email FROM emails WHERE user_id=%s"
        
        try:
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result is not None and result[0] is not None  # Проверяем наличие email
        except Error as e:
            print(f"Ошибка при проверке email: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

def add_email(user_id, username, email):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        
        query = """
            INSERT INTO emails (username, user_id, email)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE email=%s;
        """
        
        values = (username, user_id, email, email)
        
        try:
            cursor.execute(query, values)
            connection.commit()
            print("Email успешно добавлен или обновлен в БД")
        except Error as e:
            print(f"Ошибка при добавлении email: {e}")
        finally:
            cursor.close()
            connection.close()