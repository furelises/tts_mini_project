import json
import logging
import os
import time

import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

TELEGRAM_TOKEN = config['TELEGRAM_TOKEN']
FOLDER_ID = config['FOLDER_ID']

DB_FILE = config.get('DB_FILE', './storage/db.sqlite')
LOG_FILE = config.get('LOG_FILE', './storage/log_file.txt')
TOKEN_FILE = config.get('TOKEN_FILE', './storage/token_file.json')

# макс. количество пользователей на весь проект
MAX_USERS = config.get('MAX_USERS', 3)
# макс. количество токенов у пользователя
MAX_USER_GPT_TOKENS = config.get('MAX_USER_GPT_TOKENS', 2000)
# максимальное кол-во токенов в ответе GPT
MAX_GPT_TOKENS = config.get('MAX_GPT_TOKENS', 120)
# кол-во последних сообщений из диалога
COUNT_LAST_MSG = config.get('COUNT_LAST_MSG', 4)

MAX_USER_TTS_SYMBOLS = config.get('MAX_USER_TTS_SYMBOLS', 2000)
MAX_TTS_SYMBOLS = config.get('MAX_TTS_SYMBOLS', 5000)
MAX_USER_STT_BLOCKS = config.get('MAX_USER_STT_BLOCKS', 10)
MAX_STT_BLOCKS = config.get('MAX_STT_BLOCKS', 50)

SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты веселый собеседник. Общайся со мной на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй мне, что ты умеешь и можешь. '
                                            'Изображай человека'}]


def create_new_token():
    metadata_url = "169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}
    token_dir = os.path.dirname(TOKEN_FILE)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)
    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            token_data["expires_at"] = time.time() + token_data["expires_in"]
            with open(TOKEN_FILE, "w") as t_file:
                json.dump(token_data, t_file)
            logging.info("Token created")
        else:
            logging.error(f"Failed to retrieve token. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred while retrieving token: {e}")


def get_creds():
    try:
        with open(TOKEN_FILE, "r") as f:
            d = json.loads(f.read())
            expiration = d.get("expires_at")
        if expiration and expiration < time.time():
            create_new_token()
    except Exception as e:
        create_new_token()

    with open(TOKEN_FILE, "r") as f:
        d = json.loads(f.read())
        token = d["access_token"]
    return token, FOLDER_ID
