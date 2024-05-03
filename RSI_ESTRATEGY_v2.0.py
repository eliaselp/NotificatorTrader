import pickle
import os
import sys
from tradingview_ta import TA_Handler, Interval
import time
import datetime
import ccxt
import smtplib
import pandas as pd

from email.message import EmailMessage

# Configuración del servidor SMTP
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "tradingLiranza@gmail.com"
smtp_password = "gkqnjoscanyjcver"



# Función para enviar correo electrónico
def enviar_correo(s):
    destinatarios = ["liranzaelias@gmail.com"]
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
        self.interval=interval
        self.ganancia=0
        self.current_operation=None
        self.open_price=None
        self.last_rsi=None
        self.analisis=1

    
    def get_indicator(self):
        # Asegúrate de tener la última versión de ccxt que incluye BingX
        exchange_id = 'bingx'
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        # Definir el símbolo y la temporalidad
        symbol = 'BTC/USDT'
        timeframe = '1m'
        # Obtener los datos históricos usando el método fetch_ohlcv
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=500)

        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calcular EMAs
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema55'] = df['close'].ewm(span=55, adjust=False).mean()
        df['ema100'] = df['close'].ewm(span=100, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()

        # Devolver los últimos valores de las EMAs como variables separadas
        ema9 = df['ema9'].iloc[-1]
        ema21 = df['ema21'].iloc[-1]
        ema55 = df['ema55'].iloc[-1]
        ema100 = df['ema100'].iloc[-1]
        ema200 = df['ema200'].iloc[-1]

        return ema9, ema21, ema55, ema100, ema200
    

    def get_current_price(self):
        analysis = self.handler.get_analysis()
        return analysis.indicators['close']
    


    def trade(self):
        nueva=False
        print("\nPROCESANDO ANALISIS...")
        current_price = self.get_current_price()
        s=f"[#] Analisis # {self.analisis}\n"
        self.analisis+=1
        s+=f"[#] OPERACION ACTUAL: {self.current_operation}\n"
        s+=f"[#] GANANCIA ACTUAL: {self.ganancia}\n"
        s+=f"[#] PRECIO BTC-USDT: {current_price}\n"

        ema9,ema21,ema55,ema100,ema200=self.get_indicator()

        
        if self.current_operation == "LONG":
            if ema9 < ema21:
                s+=self.close_operations(current_price,s)
                nueva=True
            else:
                s+=self.mantener(current_price,s)
                #============================================
        elif self.current_operation == "SHORT":
            if ema9 > ema21:
                s+=self.close_operations(current_price,s)
                nueva=True
            else:
                s+=self.mantener(current_price,s)
                #============================================

                
        if self.current_operation == None:
            if ((ema9>ema21 and ema9>ema55 and ema9>ema100 and ema9>ema200) and (ema21>ema55 and ema21>ema100 and ema21>ema200) and current_price>ema200):
                s+=self.open_long(current_price,s)
                nueva=True
            elif ((ema9<ema21 and ema9<ema55 and ema9<ema100 and ema9<ema200) and (ema21<ema55 and ema21<ema100 and ema21<ema200) and current_price<ema200):
                s+=self.open_short(current_price,s)
                nueva=True
            else:
                s+=self.mantener(current_price,s)
                #============================================
        s+=f"[#] EMA 9: {ema9}\n"
        s+=f"[#] EMA 21: {ema21}\n"
        s+=f"[#] EMA 55: {ema55}\n"
        s+=f"[#] EMA 100: {ema100}\n"
        s+=f"[#] EMA 200: {ema200}\n"
        
        print(s)
        print("--------------------------------------\n")
        if nueva == True:
            enviar_correo(s)

    def mantener(self,current_price,s=""):
        s=""
        if self.current_operation != None:
            s+=f">>>> MANTENER OPERACION {self.current_operation} a {current_price}\n"
            s+="[#] ESTADO: "
            if self.current_operation == "LONG":
                s+=str(current_price-self.open_price)+"\n"
            else:
                s+=str(self.open_price-current_price)+"\n"
        else:
            s+="[#] NO EJECUTAR ACCION\n"
        return s



    def open_long(self,current_price,s=""):
        s=""
        s+=f">>>> ABRIENDO POSICION LONG A {current_price}\n"
        self.current_operation="LONG"
        self.open_price=current_price
        self.save_state()
        return s

    def open_short(self,current_price,s=""):
        s=""
        s+=f">>>> ABRIENDO POSICION SHORT A {current_price}\n"
        self.current_operation="SHORT"
        self.open_price=current_price
        self.save_state()
        return s

    def close_operations(self,current_price,s=""):
        s=""
        s+=f">>>> CERRANDO POSICION {self.current_operation}\n"
        if self.current_operation == "LONG":
            self.ganancia+=current_price - self.open_price
            s+=f"[#] ESTADO: {current_price - self.open_price}\n"
        else:
            self.ganancia+=self.open_price - current_price
            s+=f"[#] ESTADO: {self.open_price - current_price}\n"
        s+=f"[#] GANANCIA: {self.ganancia}\n"
        self.open_price=None
        self.current_operation=None
        self.save_state()
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


def run_bot():
    # Intentar recuperar el estado del bot
    bot = SwingTradingBot.load_state()
    if bot is None:
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
        bot = SwingTradingBot(symbol, screener, exchange, interval)
    
    # Iniciar el bot
    while True:
        os.system("cls")
        error=True
        try:
            bot.trade()
        except Exception as e:
            print(f"Error: {str(e)}\n")
            error=True
        print("Esperando para el próximo análisis...")
        tiempo_espera=0
        if error == True:
            tiempo_espera=10
        else:
            # Tiempo de espera basado en la temporalidad seleccionada
            tiempo_espera = {
                Interval.INTERVAL_1_MINUTE: 60,
                Interval.INTERVAL_15_MINUTES: 60 * 15,
                Interval.INTERVAL_30_MINUTES: 60 * 30,
                Interval.INTERVAL_1_HOUR: 60 * 60,
                Interval.INTERVAL_4_HOURS: 60 * 60 * 4,
                Interval.INTERVAL_1_DAY: 60 * 60 * 24
            }.get(interval, 60)  # Por defecto 1 minuto si la opción no es válida
        # Contador regresivo durante el tiempo de espera

        for i in range(tiempo_espera, 0, -1):
            sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
        sys.stdout.flush()
            
if __name__ == "__main__":
    run_bot()
