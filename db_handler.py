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
def insert_message(user_id, fio, username, user_message, bot_response):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = """
        INSERT INTO messages (user_id, fio, username, user_message, bot_response)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (user_id, fio, username, user_message, bot_response)
        
        try:
            cursor.execute(query, values)
            connection.commit()
            print("Данные успешно записаны в БД")
        except Error as e:
            print(f"Ошибка при вставке данных: {e}")
        finally:
            cursor.close()
            connection.close()