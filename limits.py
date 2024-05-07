import math

import config
import database
import gpt


# получаем количество уникальных пользователей, кроме самого пользователя
def check_number_of_users(user_id):
    count = database.count_users(user_id)
    if count is None:
        return None, "Ошибка при работе с БД"
    if count > config.MAX_USERS:
        return None, "Превышено максимальное количество пользователей"
    return True, ""


# проверяем, не превысил ли пользователь лимиты на общение с GPT
def is_gpt_token_limit(messages, total_spent_tokens):
    all_tokens = gpt.count_gpt_tokens(messages) + total_spent_tokens
    if all_tokens > config.MAX_USER_GPT_TOKENS:
        return None, f"Превышен общий лимит GPT-токенов {config.MAX_USER_GPT_TOKENS}"
    return all_tokens, ""


# проверяем, не превысил ли пользователь лимиты на преобразование аудио в текст
def is_stt_block_limit(user_id, duration) -> (int | None, str | None):
    # Переводим секунды в аудиоблоки
    audio_blocks = math.ceil(duration / 15)  # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = database.count_all_blocks(user_id) + audio_blocks
    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
        return None, msg

    # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks >= config.MAX_USER_STT_BLOCKS:
        msg = f"Превышен общий лимит SpeechKit STT {config.MAX_USER_STT_BLOCKS}. Использовано {all_blocks} блоков. Доступно: {config.MAX_USER_STT_BLOCKS - all_blocks}"
        return None, msg

    if audio_blocks >= config.MAX_STT_BLOCKS:
        msg = f"Превышен общий лимит на запрос SpeechKit STT {config.MAX_STT_BLOCKS}."
        return None, msg
    return audio_blocks, None


# проверяем, не превысил ли пользователь лимиты на преобразование текста в аудио
def is_tts_symbol_limit(user_id, text) -> (int | None, str | None):
    text_symbols = len(text)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = database.count_all_symbol(user_id) + text_symbols

    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= config.MAX_USER_TTS_SYMBOLS:
        msg = f"Превышен общий лимит SpeechKit TTS {config.MAX_USER_TTS_SYMBOLS}. Использовано: {all_symbols} символов. Доступно: {config.MAX_USER_TTS_SYMBOLS - all_symbols}"
        return None, msg

    # Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= config.MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит SpeechKit TTS на запрос {config.MAX_TTS_SYMBOLS}, в сообщении {text_symbols} символов"
        return None, msg
    return len(text), None
