import pickle
import os
import sys
from tradingview_ta import TA_Handler, Interval, Exchange
import time
from datetime import datetime
import smtplib
from email.message import EmailMessage
import requests

# Configuración del servidor SMTP
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "tradingLiranza@gmail.com"
smtp_password = "gkqnjoscanyjcver"

# Función para enviar correo electrónico
def enviar_correo(s):
    destinatarios = ["liranzaelias@gmail.com", "kliranza@gmail.com"]
    msg = EmailMessage()
    msg['Subject'] = 'ALERTA DE DECISION DE TRADING'
    msg['From'] = smtp_username
    msg['To'] = ", ".join(destinatarios)
    msg.set_content(s)
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Error al enviar correo: {e}")

# Clase del bot de trading
class SwingTradingBot:
    def __init__(self, symbol, screener, exchange, interval):
        self.handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=interval
        )
        self.ganancia=0
        self.last_operation = None
        self.last_price = None

    def get_current_price(self):
        analysis = self.handler.get_analysis()
        return analysis.indicators['close']

    def get_analysis(self):
        return self.handler.get_analysis()
    
    def obtener_indicadores(self):
        analysis = self.handler.get_analysis()
        ema20 = analysis.indicators['EMA20']
        ema50 = analysis.indicators['EMA50']
        adx = analysis.indicators['ADX']

        # Determinar si el RSI indica sobreventa o sobrecompra
        return ema20, ema50, adx

    def trade_decision(self, analysis):
        current_price = self.get_current_price()
        summary = analysis.summary
        indicators = analysis.indicators
        recommendation = summary['RECOMMENDATION']

        ema20, ema50, adx, = self.obtener_indicadores()
        # Verificar si hay una tendencia definida usando ADX
        if ema20 > ema50:
            if self.last_operation=="SHORT" and recommendation not in ["STRONG_SELL"]:
                self.close_position(current_price,indicators)
                if recommendation == "STRONG_BUY":
                    self.open_long_position(indicators,current_price)
            if self.last_operation!="LONG" and recommendation=='STRONG_BUY':
                self.open_long_position(indicators,current_price)
            elif self.last_operation=="LONG":
                if recommendation in ["STRONG_BUY"]:
                    s="Manteniendo la posición"
                    if self.last_operation:
                        s+=f"{self.last_operation} a {self.last_price}."
                    s+=f"\nPrecio actual BTC/USDT: {current_price}\n"
                    s+=f"Recomendacion: {recommendation}\n"
                    print(s)  
                else:
                    self.close_position(current_price,indicators)
                    if recommendation == "STRONG_SELL":
                        self.open_short_position(indicators,current_price)    
            else:
                s="No ejecutar accion."
                s+=f"\nPrecio actual BTC/USDT: {current_price}\n"
                s+=f"Recomendacion: {recommendation}"
                print(s)

        elif ema20 < ema50:
            if self.last_operation=="LONG" and recommendation not in ["STRONG_BUY"]:
                self.close_position(current_price,indicators)
            if self.last_operation!="SHORT" and recommendation=='STRONG_SELL':
                self.open_short_position(indicators,current_price)
            elif self.last_operation=="SHORT":
                if recommendation in ["STRONG_SELL"]:
                    s="Manteniendo la posición "
                    if self.last_operation!=None:
                        s+=f"{self.last_operation} a {self.last_price}."
                    s+=f"\nPrecio actual BTC/USDT: {current_price}\n"
                    s+=f"Recomendacion: {recommendation}\n"
                    print(s)
                else:
                    self.close_position(current_price,indicators)
                    if recommendation == "STRONG_BUY":
                        self.open_long_position(indicators,current_price)
            else:
                s="No ejecutar accion."
                s+=f"\nPrecio actual BTC/USDT: {current_price}\n"
                s+=f"Recomendacion: {recommendation}"
                print(s)


        else:
            s="Manteniendo la posición"
            if self.last_operation:
                s+=f"{self.last_operation} a {self.last_price}."
            s+=f"\nPrecio actual BTC/USDT: {current_price}\n"
            s+=f"Recomendacion: {recommendation}\n"
            print(s)
    def should_close_position(self, recommendation):
        return recommendation in ['SELL','STRONG_SELL'] if self.last_operation == 'LONG' \
            else recommendation in ['BUY','STRONG_BUY']

    def open_long_position(self, indicators, current_price):
        s=f"Señal de COMPRA fuerte detectada a {current_price}, abriendo posición en LONG."
        print(s)
        s+=self.print_indicators(indicators)
        #enviar_correo(s)
        self.last_operation = 'LONG'
        self.last_price = current_price
        self.save_state()

    def open_short_position(self, indicators, current_price):
        s=f"Señal de VENTA fuerte detectada a {current_price}, abriendo posición en SHORT."
        print(s)
        s+=self.print_indicators(indicators)
        #enviar_correo(s)
        self.last_operation = 'SHORT'
        self.last_price = current_price
        self.save_state()

    def close_position(self, current_price,indicators):
        s=f"Señal de {self.last_operation} cerrada a {current_price}.\n"
        s+="Diferencia: +[ganancia] -[perdida]: "
        if(self.last_operation=="SHORT"):
            s+=str(self.last_price-current_price)+"\n"
            self.ganancia+=self.last_price-current_price
        elif(self.last_operation=="LONG"):
            s+=str(current_price-self.last_price)+"\n"
            self.ganancia+=current_price-self.last_price
        print(s)
        s+=self.print_indicators(indicators)
        #enviar_correo(s)
        self.last_operation=None
        self.last_price=None
        self.save_state()

    def print_indicators(self, indicators):
        s="Detalles de los indicadores:\n"
        for key, value in indicators.items():
            s+=f"{key}: {value}\n"
        return s

    def save_state(self):
        with open('bot_state.pkl', 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load_state():
        if os.path.exists('bot_state.pkl'):
            with open('bot_state.pkl', 'rb') as file:
                return pickle.load(file)
        else:
            return None

# Función para ejecutar el bot
def run_bot():
    cont=1
    # Configuración inicial del bot
    symbol = "BTCUSDT.PS"
    screener = "crypto"
    exchange = "BINGX"
    
    # Solicitar al usuario que seleccione la temporalidad
    print("Seleccione la temporalidad:")
    print("1. 1 minuto")
    print("2. 15 minutos")
    print("3. 30 minutos")
    print("4. 1 hora")
    print("5. 4 horas")
    print("6. 1 día")
    opcion = input("Ingrese el número de la opción deseada: ")
    
    intervalos = {
        "1": Interval.INTERVAL_1_MINUTE,
        "2": Interval.INTERVAL_15_MINUTES,
        "3": Interval.INTERVAL_30_MINUTES,
        "4": Interval.INTERVAL_1_HOUR,
        "5": Interval.INTERVAL_4_HOURS,
        "6": Interval.INTERVAL_1_DAY
    }
    
    interval = intervalos.get(opcion, Interval.INTERVAL_1_MINUTE)  # Por defecto 1 minuto si la opción no es válida
    
    # Intentar recuperar el estado del bot
    bot = SwingTradingBot.load_state()
    if bot is None:
        bot = SwingTradingBot(symbol, screener, exchange, interval)
    
    # Iniciar el bot
    print("----------------------------------------------------\n")
    while True:
        print(f"\nAnalisis: {cont}")
        print(f"Ultima operacion: {bot.last_operation}")
        print(f"Ganancia actual: {bot.ganancia}")
        cont+=1        
        try:
            analysis = bot.get_analysis()
            bot.trade_decision(analysis)
        except requests.exceptions.ConnectionError:
            print("Error de conexión. Esperando para el próximo análisis...")
        except Exception as e:
            print(f"Error inesperado: {e}")
        
        # Mensaje de espera
        print("Esperando para el próximo análisis...\n---------------------------------")

        # Tiempo de espera basado en la temporalidad seleccionada
        tiempo_espera = {
            Interval.INTERVAL_1_MINUTE: 60,
            Interval.INTERVAL_15_MINUTES: 60 * 15,
            Interval.INTERVAL_30_MINUTES: 60 * 30,
            Interval.INTERVAL_1_HOUR: 60 * 60,
            Interval.INTERVAL_4_HOURS: 60 * 60 * 4,
            Interval.INTERVAL_1_DAY: 60 * 60 * 24
        }.get(interval, 60)  # Por defecto 1 minuto si la opción no es válida
        
        #time.sleep(tiempo_espera)
         
        # Contador regresivo durante el tiempo de espera
        for i in range(tiempo_espera, 0, -1):
            sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
        sys.stdout.flush()


if __name__ == "__main__":
    run_bot()
