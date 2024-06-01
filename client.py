import hashlib
import time
from urllib.parse import urlparse
import requests


import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna


class RequestsClient(object):
    HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "X-COINEX-KEY": "",
        "X-COINEX-SIGN": "",
        "X-COINEX-TIMESTAMP": "",
    }

    def __init__(self,access_id,secret_key):
        self.access_id = access_id
        self.secret_key = secret_key
        self.url = "https://api.coinex.com/v2"
        self.headers = self.HEADERS.copy()

    # Generate your signature string
    def gen_sign(self, method, request_path, body, timestamp):
        prepared_str = f"{method}{request_path}{body}{timestamp}{self.secret_key}"
        signed_str = hashlib.sha256(prepared_str.encode("utf-8")).hexdigest().lower()
        return signed_str

    def get_common_headers(self, signed_str, timestamp):
        headers = self.HEADERS.copy()
        headers["X-COINEX-KEY"] = self.access_id
        headers["X-COINEX-SIGN"] = signed_str
        headers["X-COINEX-TIMESTAMP"] = timestamp
        headers["Content-Type"] = "application/json; charset=utf-8"
        return headers

    def request(self, method, url, params={}, data=""):
        req = urlparse(url)
        request_path = req.path

        timestamp = str(int(time.time() * 1000))
        if method.upper() == "GET":
            # If params exist, query string needs to be added to the request path
            if params:
                query_params = []
                for item in params:
                    if params[item] is None:
                        continue
                    query_params.append(item + "=" + str(params[item]))
                query_string = "?{0}".format("&".join(query_params))
                request_path = request_path + query_string

            signed_str = self.gen_sign(
                method, request_path, body="", timestamp=timestamp
            )
            response = requests.get(
                url,
                params=params,
                headers=self.get_common_headers(signed_str, timestamp),
            )

        else:
            signed_str = self.gen_sign(
                method, request_path, body=data, timestamp=timestamp
            )
            response = requests.post(
                url, data, headers=self.get_common_headers(signed_str, timestamp)
            )

        if response.status_code != 200:
            raise ValueError(response.text)
        return response





access_id = "2BB2CDB4E9034D5C9EBB04041EBE5089"  # Replace with your access id
secret_key = "CA2792E400D023DAD732CA41C4ED0B98B0CC638FF77D9C65"  # Replace with your secret key
client=RequestsClient(access_id=access_id,secret_key=secret_key)


def get_data(size,temporalidad):
    request_path = "/futures/kline"
    params = {
        "market":"BTCUSDT",
        "limit":size,
        "period":temporalidad
    }
    response = client.request(
        "GET",
        "{url}{request_path}".format(url=client.url, request_path=request_path),
        params=params,
    )
    return response.json().get("data")



def identificar_patron(ohlcv_df):
    # Encontrar máximos y mínimos locales
    maximos = ohlcv_df['high'].rolling(window=5, center=True).apply(lambda x: x[2] if x[2] == x.max() else None)
    minimos = ohlcv_df['low'].rolling(window=5, center=True).apply(lambda x: x[2] if x[2] == x.min() else None)

    # Últimos precios
    ultimo_maximo = maximos.last_valid_index()
    ultimo_minimo = minimos.last_valid_index()

    # Última fila del dataframe para la señal actual
    ultimo = ohlcv_df.iloc[-1]

    # Reconocimiento de patrones
    if pd.notnull(ultimo_maximo) and pd.notnull(ultimo_minimo):
        if ultimo_maximo > ultimo_minimo:
            # El último máximo es más reciente que el último mínimo
            if ultimo['close'] > ohlcv_df.loc[ultimo_maximo, 'high']:
                return 'compra'  # Rompimiento alcista
            elif ultimo['close'] < ohlcv_df.loc[ultimo_minimo, 'low']:
                return 'venta'  # Rompimiento bajista
            else:
                return 'lateralizacion'  # Sin rompimiento claro
        elif ultimo_minimo > ultimo_maximo:
            # El último mínimo es más reciente que el último máximo
            if ultimo['close'] < ohlcv_df.loc[ultimo_minimo, 'low']:
                return 'venta'  # Rompimiento bajista
            elif ultimo['close'] > ohlcv_df.loc[ultimo_maximo, 'high']:
                return 'compra'  # Rompimiento alcista
            else:
                return 'lateralizacion'  # Sin rompimiento claro
    else:
        return 'lateralizacion'  # No se encontraron patrones claros

data=list(get_data(1000,"1min"))
ohlcv_df = pd.DataFrame(data)
# Convertir las columnas de precios y volumen a numérico
ohlcv_df['close'] = pd.to_numeric(ohlcv_df['close'])
ohlcv_df['high'] = pd.to_numeric(ohlcv_df['high'])
ohlcv_df['low'] = pd.to_numeric(ohlcv_df['low'])
ohlcv_df['open'] = pd.to_numeric(ohlcv_df['open'])
ohlcv_df['volume'] = pd.to_numeric(ohlcv_df['volume'])

# Uso del método
senal = identificar_patron(ohlcv_df)
print(f"La señal generada es: {senal}")

