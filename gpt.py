import logging

import requests

import config


class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content


# Подсчитывает количество токенов в тексте
def count_gpt_tokens(messages: list[dict]) -> int:
    token, folder_id = config.get_creds()
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "messages": messages
    }
    logging.info(f"tokenize request: {data}")
    try:
        return len(requests.post(url=url, json=data, headers=headers).json()['tokens'])
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return 0


def ask_gpt(messages: list[dict]) -> (bool, str, int | None):
    token, folder_id = config.get_creds()
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": config.MAX_GPT_TOKENS
        },
        "messages": config.SYSTEM_PROMPT + messages
    }
    try:
        logging.info(f"gpt request: {data}")
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logging.error('Ошибка запроса к gpt: %s', response.status_code)
            return False, f"Status code {response.status_code}", None
        answer = response.json()['result']['alternatives'][0]['message']['text']
        tokens_in_answer = count_gpt_tokens([{'role': 'assistant', 'text': answer}])
        return True, answer, tokens_in_answer
    except Exception as e:
        logging.error('Ошибка запроса к gpt: %s', repr(e))
        return False, "Произошла непредвиденная ошибка. Подробности см. в журнале.", None
