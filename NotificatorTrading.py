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
        self.open_price = None
        self.last_price=None
        self.last_max=None
        self.last_rsi=None
        self.last_stoploss=None
        self.riesgo=0.005
    def obtener_indicadores(self):
        analysis = self.handler.get_analysis()
        # Bollinger Bands
        bollinger_upper = analysis.indicators['BB.upper']
        bollinger_lower = analysis.indicators['BB.lower']
        # Para la banda media, puedes usar la EMA o SMA con la longitud correspondiente
        bollinger_middle = analysis.indicators['EMA20']  # o 'SMA20' si prefieres SMA
        # RSI con longitud 13
        rsi = analysis.indicators['RSI']
        return bollinger_upper, bollinger_middle, bollinger_lower, rsi, bollinger_middle

    
    def get_current_price(self):
        analysis = self.handler.get_analysis()
        return analysis.indicators['close']

    

    def trade_decision(self):
        current_price = self.get_current_price()
        bollinger_upper, bollinger_middle, bollinger_lower, rsi, ema30 = self.obtener_indicadores()
        if self.last_rsi==None:
            self.last_rsi=rsi
        if self.last_price==None:
            self.last_price=current_price
        # Calcular la distancia entre las bandas de Bollinger
        distancia_bandas = bollinger_upper - bollinger_lower
        # Definir un umbral de volatilidad (ajustar según preferencia)
        umbral_volatilidad = ema30 * 0.003  # Ejemplo: 7% de la EMA30
        print(f"Indice de volatilidad: {distancia_bandas-umbral_volatilidad}")
        #print(f"DISTANDIA DE BANDAS {distancia_bandas}")
        #print(f"Humbral: {umbral_volatilidad}")
        if(self.last_operation!=None):
            if(self.last_operation=="LONG"):
                if current_price <= self.stoploss:
                    self.close_position(current_price,True)
            elif(self.last_operation=="SHORT"):
                if current_price >= self.stoploss:
                    self.close_position(current_price,True)

        if distancia_bandas > umbral_volatilidad:
            if current_price < ema30:
                if self.last_rsi <= 30 and rsi > self.last_rsi:
                    if self.last_operation == None:
                        self.open_long_position(current_price)
                    elif self.last_operation == "SHORT":
                        self.close_position(current_price)
                        self.open_long_position(current_price)
                    else:
                        self.mantener_posicion(current_price)
                else:
                    if self.last_operation == "LONG":
                        if self.last_rsi >= 70 and rsi < self.last_rsi:
                            self.close_position(current_price)
                            self.open_short_position(current_price)
                        else:
                            self.mantener_posicion(current_price)
                    else:
                        self.mantener_posicion(current_price)
            elif current_price > ema30:
                if self.last_rsi >= 70 and rsi < self.last_rsi:
                    if self.last_operation == None:
                        self.open_short_position(current_price)
                    elif self.last_operation=="LONG":
                        self.close_position(current_price)
                        self.open_short_position(current_price)
                    else:
                        self.mantener_posicion(current_price)
                else:
                    if self.last_operation == "SHORT":
                        if self.last_rsi <= 30 and rsi > self.last_rsi:
                            self.close_position(current_price)
                            self.open_long_position(current_price)
                        else:
                            self.mantener_posicion(current_price)
                    else:
                        self.mantener_posicion(current_price)
            else:
                self.mantener_posicion(current_price)
        else:
            print("ZONA DE LATERIZACION O RANGO.")
            if self.last_operation!=None:
                self.close_position(current_price)
        self.last_rsi=rsi
        self.last_price=current_price
        print(f"Precio Actual BTC/USDT: {current_price}")
        print(f"EMA20: {ema30}")
        print(f"RSI: {rsi}")

    def mantener_posicion(self,current_price):
        if self.last_operation==None:
            print("No realizar ninguna accion")
        else:
            print(f"Manteniendo la posicion {self.last_operation} en {self.open_price}")
            if(self.last_operation=="SHORT"):
                print(f"Estado: {str(self.open_price-current_price)}")
                if current_price < self.last_max:
                    self.stoploss -= self.last_price-current_price
                    self.last_max = current_price
            elif(self.last_operation=="LONG"):
                print(f"Estado: {str(current_price-self.open_price)}")
                if current_price > self.last_max:
                    self.stoploss += current_price - self.last_operation
                    self.last_max = current_price
            print(f"STOPLOSS: {self.stoploss}")


    def open_long_position(self, current_price,s=""):
        s+=f"Señal de COMPRA fuerte detectada a {current_price},\nAbriendo posición en LONG."
        print(s)
        s+=f"\nGanancia actual: {self.ganancia}"
        enviar_correo(s)
        self.last_operation = 'LONG'
        self.open_price = current_price
        self.last_max=current_price
        self.stoploss=current_price-(current_price*self.riesgo)
        self.save_state()

    def open_short_position(self, current_price,s=""):
        s+=f"Señal de VENTA fuerte detectada a {current_price},\nAbriendo posición en SHORT."
        print(s)
        s+=f"\nGanancia actual: {self.ganancia}"
        enviar_correo(s)
        self.last_operation = 'SHORT'
        self.open_price = current_price
        self.last_max = current_price
        self.stoploss = current_price+(current_price*self.riesgo)
        self.save_state()

    def close_position(self, current_price,stop=False):
        s=""
        if stop==True:
            s+="SEÑAL DE STOPLOSS DISPARADA\n"
        s+=f"Señal de {self.last_operation} cerrada a {current_price}.\n"
        s+="Diferencia: +[ganancia] -[perdida]: "
        if(self.last_operation=="SHORT"):
            s+=str(self.open_price-current_price)+"\n"
            self.ganancia+=self.open_price-current_price
        elif(self.last_operation=="LONG"):
            s+=str(current_price-self.open_price)+"\n"
            self.ganancia+=current_price-self.open_price
        print(s)
        s+=f"\nGanancia actual: {self.ganancia}"
        enviar_correo(s)
        self.last_operation=None
        self.open_price=None
        self.last_max=None
        self.save_state()

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
    print("----------------------------------------\n")
    while True:
        error=False
        print(f"\nAnalisis: {cont}")
        print(f"Ultima operacion: {bot.last_operation}")
        print(f"Ganancia actual: {bot.ganancia}")
        cont+=1 
        try:
            bot.trade_decision()
        except requests.exceptions.ConnectionError:
            print("Error de conexión.")
            error=True
        #except Exception as e:
        #    print(f"Error inesperado: {e}")
        #    error=True

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
        
        if error == True:
            for i in range(10, 0, -1):
                sys.stdout.write("\rTiempo restante: 00:{:02d} ".format(i))
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
            sys.stdout.flush()
        else:
            # Contador regresivo durante el tiempo de espera
            for i in range(tiempo_espera, 0, -1):
                sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
            sys.stdout.flush()


if __name__ == "__main__":
    run_bot()
