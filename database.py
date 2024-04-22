import logging
import sqlite3

import config


def create_table():
    db_name = config.db_file
    try:
        # Создаём подключение к базе данных
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Создаём таблицу messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                tts_symbols INTEGER,
                stt_blocks INTEGER)
            ''')
            # Сохраняем изменения
            conn.commit()
    except Exception as e:
        logging.error("create table: {e}")


def insert_tts(user_id, message, value):
    logging.info(f"insert_tts: (user_id: {user_id}, message: {message}, value: {value}")
    insert_row(user_id, message, 'tts_symbols', value)


def insert_stt(user_id, message, value):
    logging.info(f"insert_stt: (user_id: {user_id}, message: {message}, value: {value}")
    insert_row(user_id, message, 'stt_blocks', value)


def insert_row(user_id, message, cell, value):
    db_name = config.db_file
    try:
        # Создаем подключение к базе данных
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Вставляем в таблицу сообщение и заполняем ячейку cell значением value
            cursor.execute(f'''INSERT INTO messages (user_id, message, {cell}) VALUES (?, ?, ?)''',
                           (user_id, message, value))
            # Сохраняем изменения
            conn.commit()
    except Exception as e:
        logging.error(f"insert_row {e}")


def count_all_symbol(user_id):
    db_name = config.db_file
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(tts_symbols) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            # Проверяем data на наличие хоть какого-то полученного результата запроса
            # И на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # Если результат есть и data[0] == какому-то числу, то
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                # Результата нет, так как у нас ещё нет записей о потраченных символах
                return 0  # возвращаем 0
    except Exception as e:
        logging.error(f"count_all_symbol {e}")


def count_all_blocks(user_id):
    db_name = config.db_file
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(stt_blocks) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            # Проверяем data на наличие хоть какого-то полученного результата запроса
            # И на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # Если результат есть и data[0] == какому-то числу, то
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                # Результата нет, так как у нас ещё нет записей о потраченных символах
                return 0  # возвращаем 0
    except Exception as e:
        logging.error(f"count_all_blocks {e}")
