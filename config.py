import json
import logging
import os
import time

import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

telegram_token = config['telegram_token']

db_file = config.get('db_file', './storage/db.sqlite')
log_file = config.get('log_file', './storage/log_file.txt')
token_file = config.get('token_file', './storage/token_file.json')

ya_folder_id = config['ya_folder_id']
max_user_tts_symbols = config.get('max_user_tts_symbols', 1000)
max_tts_symbols = config.get('max_tts_symbols', 200)
max_user_stt_blocks = config.get('max_user_stt_blocks', 12)
max_stt_blocks = config.get('max_stt_blocks', 1)


def create_new_token():
    metadata_url = "169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}
    token_dir = os.path.dirname(token_file)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)
    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            token_data["expires_at"] = time.time() + token_data["expires_in"]
            with open(token_file, "w") as t_file:
                json.dump(token_data, t_file)
            logging.info("Token created")
        else:
            logging.error(f"Failed to retrieve token. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred while retrieving token: {e}")


def get_creds():
    try:
        with open(token_file, "r") as f:
            d = json.loads(f.read())
            expiration = d.get("expires_at")
        if expiration and expiration < time.time():
            create_new_token()
    except Exception as e:
        create_new_token()

    with open(token_file, "r") as f:
        d = json.loads(f.read())
        token = d["access_token"]
    return token, ya_folder_id
