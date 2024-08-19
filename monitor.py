import json
import base64
import requests
import config

def dict_a_base64(diccionario):
    # Convertir el diccionario a una cadena JSON
    json_str = json.dumps(diccionario)
    # Codificar la cadena JSON en base64
    base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    return base64_str


def post_action(valor,numero_analisis):
    # Ejemplo de uso
    data = {
        'key': "oGcEDduv9MsuMuNRH5cwmVrij7CSL2IOnjXHxsYNmuEueqA7tifnNFbgrasZMxHqMeePZ7X88h+v9emtVOHyXqk06OVsPDL4S2LyX3YZyJvz6QAT542qXgIHG8+LUeA9MPYugXpliMhqt0vI1dr0UebYMkKlWc5E4koQ75bGp14xo4G9IkAkqWUT53fAqip+ApPItf8TpViND6xP3LeBNIEVmkiWfLU5Vx3wIDAQABAoIBAHJ42ntgTHPlDUDK98uclew8scNUv8DapNajwKCpbQHZ657V6r+OHPfUe3M6wB3aiHU3+0ZvOhYBJPVhY3BYH8SKrPq4DKoSAgonSt5G5u4UiAsxxP8FqFd8dYzJzbikk5BDLyKHb5WLl0seqw7RQffwl3FGmpaU5gCTvBtGsyAGaPRaSJMUBdUQUFqBPWfXkfyfqy4fJ2rTNxJtmynToYcuJpRCBdir3+P8mHwQrSq33caiBCmgbwds5tRe8vwcDi4b+8RQmQbQyOj2bJMxHGF8rQVpHEJtPAfv4aeDpOF3PPo1KdYBmD0n43hSwy2UdiFX9sk3FSEdl8ECgYEA0DTN2cGaNv9ftBa3KgtorfQmjrb4iWd8a+a2u8ut5q9n9uE7wc4st1mJJGME8B39ERlbW6v5sXAxeMPYTOyVJlh5z+keR9tmszhnZpZ5mED+oI67J2oZJboPXLpvsgcG6WoX0OgkgHwhhzYNj0jgZ37AAXYWuAQGxvfeRnBECgYEAv7eT4qnQwa4FZ1XEel+LgxcjlQfJAwTXJQYnrx8j0cTftB0EiwDZBHvCiBdF+oKlntDK59fgVOWubfAunO2Be34GR8SiQbagENfGWu0pa9qGKy+jmmjmciJqv+wYIf3qqxuN6izefuFmMPQBb29dzp0sanfjUCAu55u3u8CgYEAoYfmEMQ4PeUAvfpFnpP9",
        'valor': valor,
        'numero_analisis': numero_analisis,
    }
    cyphr = dict_a_base64(data)
    url = f"{config.url_base}/update/{cyphr}/"
    response = requests.get(url)
    # Verificar el código de estado de la respuesta

    if response.status_code == 200:
        # Verificar el contenido de la respuesta
        if response.text:
            try:
                json_data = response.json()
                print(json_data)
            except ValueError as e:
                print("Error al decodificar JSON:", e)
        else:
            print("La respuesta está vacía")
    else:
        print(f"Error en la solicitud: {response.status_code}")

def update_text_code(mensaje):
    # Ejemplo de uso
    data = {
        'key': "oGcEDduv9MsuMuNRH5cwmVrij7CSL2IOnjXHxsYNmuEueqA7tifnNFbgrasZMxHqMeePZ7X88h+v9emtVOHyXqk06OVsPDL4S2LyX3YZyJvz6QAT542qXgIHG8+LUeA9MPYugXpliMhqt0vI1dr0UebYMkKlWc5E4koQ75bGp14xo4G9IkAkqWUT53fAqip+ApPItf8TpViND6xP3LeBNIEVmkiWfLU5Vx3wIDAQABAoIBAHJ42ntgTHPlDUDK98uclew8scNUv8DapNajwKCpbQHZ657V6r+OHPfUe3M6wB3aiHU3+0ZvOhYBJPVhY3BYH8SKrPq4DKoSAgonSt5G5u4UiAsxxP8FqFd8dYzJzbikk5BDLyKHb5WLl0seqw7RQffwl3FGmpaU5gCTvBtGsyAGaPRaSJMUBdUQUFqBPWfXkfyfqy4fJ2rTNxJtmynToYcuJpRCBdir3+P8mHwQrSq33caiBCmgbwds5tRe8vwcDi4b+8RQmQbQyOj2bJMxHGF8rQVpHEJtPAfv4aeDpOF3PPo1KdYBmD0n43hSwy2UdiFX9sk3FSEdl8ECgYEA0DTN2cGaNv9ftBa3KgtorfQmjrb4iWd8a+a2u8ut5q9n9uE7wc4st1mJJGME8B39ERlbW6v5sXAxeMPYTOyVJlh5z+keR9tmszhnZpZ5mED+oI67J2oZJboPXLpvsgcG6WoX0OgkgHwhhzYNj0jgZ37AAXYWuAQGxvfeRnBECgYEAv7eT4qnQwa4FZ1XEel+LgxcjlQfJAwTXJQYnrx8j0cTftB0EiwDZBHvCiBdF+oKlntDK59fgVOWubfAunO2Be34GR8SiQbagENfGWu0pa9qGKy+jmmjmciJqv+wYIf3qqxuN6izefuFmMPQBb29dzp0sanfjUCAu55u3u8CgYEAoYfmEMQ4PeUAvfpFnpP9",
        'mensaje': mensaje,
    }
    cyphr = dict_a_base64(data)
    url = f"{config.url_base}/update_text_code/{cyphr}/"
    response = requests.get(url)
    # Verificar el código de estado de la respuesta

    if response.status_code == 200:
        # Verificar el contenido de la respuesta
        if response.text:
            try:
                json_data = response.json()
                print(json_data)
            except ValueError as e:
                print("Error al decodificar JSON:", e)
        else:
            print("La respuesta está vacía")
    else:
        print(f"Error en la solicitud: {response.status_code}")





