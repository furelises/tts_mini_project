import math

import telebot

import config
import database
import stt
import tts

bot = telebot.TeleBot(token=config.telegram_token)


@bot.message_handler(commands=['start'])
def start_function(message):
    user_id = message.from_user.id
    bot.send_message(user_id,
                     "Привет! Запиши мне текст и я тебе отвечу, после команды /tts  или  запиши мне аудио после команды /stt )))")


@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tt_speach)


def tt_speach(message):
    user_id = message.from_user.id
    text = message.text

    if message.content_type != 'text':
        bot.send_message(user_id, 'Отправь текстовое сообщение')
        return
    text_symbol = is_tts_symbol_limit(message, text)
    if text_symbol is None:
        return

    # Записываем сообщение и кол-во символов в БД
    database.insert_tts(user_id, text, text_symbol)
    status, content = tts.text_to_speech(text)

    # Если статус True - отправляем голосовое сообщение, иначе - сообщение об ошибке
    if status:
        bot.send_voice(user_id, content)
    else:
        bot.send_message(user_id, content)


def is_tts_symbol_limit(message, text):
    user_id = message.from_user.id
    text_symbols = len(text)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = database.count_all_symbol(user_id) + text_symbols

    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= config.max_user_tts_symbols:
        msg = f"Превышен общий лимит SpeechKit TTS {config.max_user_tts_symbols}. Использовано: {all_symbols} символов. Доступно: {config.max_user_tts_symbols - all_symbols}"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= config.max_tts_symbols:
        msg = f"Превышен лимит SpeechKit TTS на запрос {config.max_tts_symbols}, в сообщении {text_symbols} символов"
        bot.send_message(user_id, msg)
        return None
    return len(text)


# Обрабатываем команду /stt
@bot.message_handler(commands=['stt'])
def stt_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, speach_tt)


def speach_tt(message):
    user_id = message.from_user.id

    # Проверка, что сообщение действительно голосовое
    if not message.voice:
        return

    # Считаем аудиоблоки и проверяем сумму потраченных аудиоблоков
    stt_blocks = is_stt_block_limit(message, message.voice.duration)
    if not stt_blocks:
        return

    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение

    # Получаем статус и содержимое ответа от SpeechKit
    status, text = stt.speech_to_text(file)  # преобразовываем голосовое сообщение в текст

    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        # Записываем сообщение и кол-во аудиоблоков в БД
        database.insert_stt(user_id, text, stt_blocks)
        bot.send_message(user_id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, text)


def is_stt_block_limit(message, duration):
    user_id = message.from_user.id

    # Переводим секунды в аудиоблоки
    audio_blocks = math.ceil(duration / 15)  # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = database.count_all_blocks(user_id) + audio_blocks
    # max_stt_blocks = config.max_stt_blocks
    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks >= config.max_user_stt_blocks:
        msg = f"Превышен общий лимит SpeechKit STT {config.max_user_stt_blocks}. Использовано {all_blocks} блоков. Доступно: {config.max_user_stt_blocks - all_blocks}"
        bot.send_message(user_id, msg)
        return None

    if audio_blocks >= config.max_stt_blocks:
        msg = f"Превышен общий лимит на запрос SpeechKit STT {config.max_stt_blocks}. "
        bot.send_message(user_id, msg)
        return None


database.create_table()
bot.polling()
