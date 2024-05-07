import logging
import os

import telebot

import config
import database
import gpt
import limits
import stt
import tts

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
bot = telebot.TeleBot(token=config.TELEGRAM_TOKEN)


# обрабатываем команду /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.from_user.id,
                     "Привет! Я голосовой собеседник. "
                     "Могу общаться на любые темы. Отправь мне голосовое сообщение или текст, и я тебе отвечу!")


# обрабатываем команду /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.from_user.id, "Чтобы приступить к общению, отправь мне голосовое сообщение или текст")


@bot.message_handler(commands=['debug'])
def debug_command(message):
    if os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, f"Файл {config.LOG_FILE} не найден.")


@bot.message_handler(commands=['tts'])
def tts_command(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts_handler)


def tts_handler(message):
    user_id = message.from_user.id
    text = message.text

    if message.content_type != 'text':
        bot.send_message(user_id, 'Отправь текстовое сообщение')
        return

    status, content = tts.text_to_speech(text)
    # Если статус True - отправляем голосовое сообщение, иначе - сообщение об ошибке
    if status:
        bot.send_voice(user_id, content)
    else:
        bot.send_message(user_id, content)


# Обрабатываем команду /stt
@bot.message_handler(commands=['stt'])
def stt_command(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt_handler)


def stt_handler(message):
    user_id = message.from_user.id

    # Проверка, что сообщение действительно голосовое
    if not message.voice:
        bot.send_message(user_id, 'Отправь голосовое сообщение')
        return

    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение

    # Получаем статус и содержимое ответа от SpeechKit
    status, text = stt.speech_to_text(file)  # преобразовываем голосовое сообщение в текст
    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        bot.send_message(user_id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, text)


# обрабатываем голосовые сообщения
@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    user_id = message.from_user.id
    try:
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = limits.check_number_of_users(user_id)
        if not status_check_users:
            # Если количество пользователей превышает максимально допустимое,
            # отправляем сообщение с ошибкой пользователю и прекращаем выполнение функции
            bot.send_message(user_id, error_message)
            return

        # ВАЛИДАЦИЯ_АУДИО: проверяем количество аудиоблоков
        stt_blocks, error_message = limits.is_stt_block_limit(user_id, message.voice.duration)
        # Проверка условия: если есть сообщение об ошибке (что указывает на превышение лимита аудиоблоков)
        if error_message:
            # Отправляем пользователю сообщение с ошибкой, указывающей на превышение лимита
            bot.send_message(user_id, error_message)
            # Прерываем выполнение функции, чтобы не продолжать с обработкой запроса
            return

        # Получение информации о голосовом файле и его загрузка
        file_id = message.voice.file_id  # Идентификатор голосового файла в сообщении
        file_info = bot.get_file(file_id)  # Получение информации о файле для загрузки
        file = bot.download_file(file_info.file_path)  # Загрузка файла по указанному пути
        # Преобразование голосового сообщения в текст с помощью SpeechKit
        status_stt, stt_text = stt.speech_to_text(file)  # Обращение к функции speech_to_text для получения текста
        if not status_stt:
            # Отправка сообщения об ошибке, если преобразование не удалось
            bot.send_message(user_id, stt_text)
            return

        database.add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])

        # Отправка нескольких последних сообщений от пользователя в GPT для генерации ответа
        # В константе COUNT_LAST_MSG хранится количество сообщений пользователя, которые передаем
        last_messages, total_spent_tokens = database.select_n_last_messages(user_id, config.COUNT_LAST_MSG)
        # ВАЛИДАЦИЯ GPT: подсчет токенов
        # Вызываем функцию для проверки лимита GPT-токенов, которая возвращает текущее количество использованных
        # токенов и сообщение об ошибке, если лимит превышен
        total_gpt_tokens, error_message = limits.is_gpt_token_limit(last_messages, total_spent_tokens)
        # Проверяем, вернулась ли ошибка
        if error_message:
            # Если да, отправляем пользователю сообщение с ошибкой, указывающей на превышение лимита токенов GPT
            bot.send_message(user_id, error_message)
            # Прекращаем дальнейшую обработку сообщения, чтобы не нарушать лимиты использования ресурсов
            return

        status_gpt, answer_gpt, tokens_in_answer = gpt.ask_gpt(last_messages)  # Обращение к GPT с запросом
        if not status_gpt:
            # Отправка сообщения об ошибке, если GPT не смог сгенерировать ответ
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        # ВАЛИДАЦИЯ_АУДИО: проверка символов для ответа
        # Вызываем функцию для проверки лимита символов, необходимых для преобразования текста в речь через SpeechKit
        tts_symbols, error_message = limits.is_tts_symbol_limit(user_id, answer_gpt)
        # Проверяем, вернулась ли ошибка
        database.add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])
        if error_message:
            # Если да, отправляем пользователю сообщение с ошибкой, указывающей на превышение лимита символов для синтеза речи
            bot.send_message(user_id, error_message)
            # Прекращаем дальнейшую обработку сообщения, чтобы избежать превышения допустимого лимита
            return

        # Преобразование текстового ответа от GPT в голосовое сообщение
        status_tts, voice_response = tts.text_to_speech(
            answer_gpt)  # Обращение к функции text_to_speech для получения аудио
        if not status_tts:
            # Отправка текстового ответа GPT, если преобразование в аудио не удалось
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
        else:
            # Отправка голосового сообщения, если преобразование в аудио прошло успешно
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)

    except Exception as e:
        # Логирование ошибки
        logging.error(e)
        # Уведомление пользователя о непредвиденной ошибке
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    try:
        # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = limits.check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return

        # БД: добавляем сообщение пользователя и его роль в базу данных
        full_user_message = [message.text, 'user', 0, 0, 0]
        database.add_message(user_id=user_id, full_message=full_user_message)

        # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
        # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = database.select_n_last_messages(user_id, config.COUNT_LAST_MSG)
        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = limits.is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, error_message)
            return

        # GPT: отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = gpt.ask_gpt(last_messages)
        # GPT: обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer

        # БД: добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        database.add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


# обрабатываем все остальные типы сообщений
@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.from_user.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")


database.create_table()
bot.polling()
