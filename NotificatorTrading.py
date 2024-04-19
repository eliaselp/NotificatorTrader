'''
crear entorno virtual

pip install tradingview_ta
'''

import time
from datetime import datetime
from tradingview_ta import TA_Handler, Interval, Exchange
import smtplib
from email.message import EmailMessage
import requests

# Configuración del manejador de TradingView TA para BTC/USDT
ta_handler = TA_Handler(
    symbol="BTCUSDT",
    screener="crypto",
    exchange="BINANCE",
    interval=Interval.INTERVAL_30_MINUTES
)

# Configuración del servidor de correo electrónico
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "tradingLiranza@gmail.com"
smtp_password = "gkqnjoscanyjcver"

# Estado global de la última operación realizada
estado_operacion = "MANTENER"  # Puede ser "COMPRAR", "VENDER" o "MANTENER"

# Función para enviar correo electrónico
def enviar_correo(accion, precio_actual):
    if accion in ["COMPRAR", "VENDER"]:
        msg = EmailMessage()
        msg['Subject'] = 'ALERTA DE DECISION DE TRADING'
        msg['From'] = smtp_username
        msg['To'] = "liranzaelias@gmail.com"
        msg.set_content(f"La decisión de trading tomada a las {datetime.now().strftime('%A, %d de %B de %Y, %I:%M %p')} es: {accion}\nPrecio actual de BTC/USDT: {precio_actual}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

# Función para obtener el precio actual de BTC/USDT
def obtener_precio_actual():
    response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
    precio = response.json()['price']
    return float(precio)

# Función para obtener el resumen de análisis técnico de TradingView
def obtener_resumen_analisis():
    analysis = ta_handler.get_analysis()
    return analysis.summary

# Función para determinar la acción de trading
def decidir_accion(resumen_analisis):
    global estado_operacion
    comprar = resumen_analisis['BUY']
    neutrales = resumen_analisis['NEUTRAL']
    vender = resumen_analisis['SELL']
    
    if comprar > vender and comprar > neutrales and estado_operacion != "COMPRAR":
        estado_operacion = "COMPRAR"
        return "COMPRAR"
    elif vender > comprar and vender > neutrales and estado_operacion != "VENDER":
        estado_operacion = "VENDER"
        return "VENDER"
    else:
        return "MANTENER"

# Función para imprimir el estado actual y la decisión de trading
def imprimir_decision(accion):
    precio_actual = obtener_precio_actual()
    if accion in ["COMPRAR", "VENDER"]:
        print(f"Decisión de trading a las {datetime.now().strftime('%A, %d de %B de %Y, %I:%M %p')}: {accion}")
        print(f"Precio actual de BTC/USDT: {precio_actual}")
        enviar_correo(accion, precio_actual)

# Función principal que ejecuta el script
def main():
    while True:
        resumen_analisis = obtener_resumen_analisis()
        accion = decidir_accion(resumen_analisis)
        imprimir_decision(accion)
        time.sleep(1800)  # Espera 30 minutos antes de la próxima ejecución

if __name__ == "__main__":
    main()
