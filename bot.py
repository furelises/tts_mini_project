import telebot
import database
import config
import tts

bot = telebot.TeleBot(token=config.telegram_token)

@bot.message_handler(commands=['start'])
def start_function(message):
    user_id = message.from_user.id
    bot.send_message(user_id,"Пивет! Запиши мне текст и я тебе отвечу, после команды /tts !)))")
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
    database.insert_row(user_id, text, text_symbol)
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


database.create_table()
bot.polling()
