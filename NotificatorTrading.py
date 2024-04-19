'''
crear entorno virtual

pip install tradingview_ta
'''

import time
from tradingview_ta import TA_Handler, Interval, Exchange
import smtplib
from email.message import EmailMessage

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

# Función para enviar correo electrónico
def enviar_correo(accion):
    msg = EmailMessage()
    msg['Subject'] = 'ALERTA DE DECISION DE TRADING'
    msg['From'] = smtp_username
    msg['To'] = "liranzaelias@gmail.com"
    msg.set_content(f"La decisión de trading tomada a las {time.datetime.now()} es: {accion}")
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)

# Función para obtener el resumen de análisis técnico de TradingView
def obtener_resumen_analisis():
    analysis = ta_handler.get_analysis()
    return analysis.summary

# Función para determinar la acción de trading
def decidir_accion(resumen_analisis):
    comprar = resumen_analisis['BUY']
    neutrales = resumen_analisis['NEUTRAL']
    vender = resumen_analisis['SELL']
    
    if comprar > vender and comprar > neutrales:
        return "COMPRAR"
    elif vender > comprar and vender > neutrales:
        return "VENDER"
    else:
        return "MANTENER"

# Función para imprimir el estado actual y la decisión de trading
def imprimir_decision(accion):
    print(f"Decisión de trading a las {time.datetime.now()}: {accion}")
    enviar_correo(accion)

# Función principal que ejecuta el script
def main():
    while True:
        resumen_analisis = obtener_resumen_analisis()
        accion = decidir_accion(resumen_analisis)
        imprimir_decision(accion)
        time.sleep(1800)  # Espera 30 minutos antes de la próxima ejecución

if __name__ == "__main__":
    main()
