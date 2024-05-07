import requests
import config


def speech_to_text(data) -> (bool, str | None):
    # iam_token, folder_id для доступа к Yandex SpeechKit
    iam_token, folder_id = config.get_creds()

    # Указываем параметры запроса
    params = "&".join([
        "topic=general",  # используем основную версию модели
        f"folderId={folder_id}",
        "lang=ru-RU"  # распознаём голосовое сообщение на русском языке
    ])

    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }

    # Выполняем запрос
    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=data
    )

    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
    else:
        return False, "При запросе в SpeechKit возникла ошибка"


if __name__ == "__main__":
    # Укажи путь к аудиофайлу, который хочешь распознать
    audio_file_path = "C:\\Users\\sofy\\Downloads\\grab\\ol2\\grisha.ogg"

    # Открываем аудиофайл в бинарном режиме чтения
    with open(audio_file_path, "rb") as audio_file:
        audio_data = audio_file.read()

    # Вызываем функцию распознавания речи
    success, result = speech_to_text(audio_data)

    # Проверяем успешность распознавания и выводим результат
    if success:
        print("Распознанный текст: ", result)
    else:
        print("Ошибка при распознавании речи: ", result)
