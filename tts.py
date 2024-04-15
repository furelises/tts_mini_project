import requests

import config

def text_to_speech(text: str):
    # Токен, Folder_id для доступа к Yandex SpeechKit
    iam_token, folder_id = config.get_creds()
    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    data = {
        'text': text,  # текст, который нужно преобразовать в голосовое сообщение
        'lang': 'ru-RU',  # язык текста - русский
        'voice': 'filipp',  # голос Филлипа
        'folderId': folder_id,
    }
    # Выполняем запрос
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)

    if response.status_code == 200:
        return True, response.content  # Возвращаем голосовое сообщение
    else:
        return False, "При запросе в SpeechKit возникла ошибка"


if __name__ == "__main__":
    # Текст, который хочешь преобразовать в голос
    text = "Привет! Я учусь работать с API SpeechKit. Это очень интересно!"

    # Вызываем функцию и получаем результат
    success, response = text_to_speech(text)

    if success:
        # Если все хорошо, сохраняем аудио в файл
        with open("output.ogg", "wb") as audio_file:
            audio_file.write(response)
        print("Аудиофайл успешно сохранен как output.ogg")
    else:
        # Если возникла ошибка, выводим сообщение об ошибке
        print("Ошибка:", response)


