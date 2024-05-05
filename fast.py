import pickle
import os
import sys
import time
import ccxt
import smtplib
import pandas as pd
from email.message import EmailMessage

# Configuración del servidor SMTP
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "tradingLiranza@gmail.com"
smtp_password = "gkqnjoscanyjcver"

def clear_console():
    # 'cls' para Windows, 'clear' para Linux y otros sistemas Unix
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)

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
    def __init__(self):
        self.exchange = ccxt.bingx({
            'apiKey': 'xnrhBImnWXQNvD5e0w5ePULBKBTv1LcUpNDLiJ9NOz9DX1Xjs06ANwk0YfT3BSFXuSSdxyUk8jUYuzh2Rg1N2g',
            'secret': 'FLl5A06TyW3d9iYTPGBgnU3uAVLqTU9yLsvLIpjAlqsMa3C9eGEZGATWrauXPoYmFRQG4SNhhsjOdM70S8LO4A',
        })
        self.simbol="BTC/USDT"
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
        symbol = self.simbol
        timeframe = '1m'
        # Obtener los datos históricos usando el método fetch_ohlcv
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=500)

        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calcular EMAs
        df['ema5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['ema15'] = df['close'].ewm(span=15, adjust=False).mean()

        # Devolver los últimos valores de las EMAs como variables separadas
        ema5 = df['ema5'].iloc[-1]
        ema15 = df['ema15'].iloc[-1]
        
        return ema5, ema15
    

    
    def get_current_price(self):
        markets = self.exchange.load_markets()
        self.exchange.load_time_difference()
        ticker = self.exchange.fetch_ticker("BTC/USDT")
        return ticker['last']  # Precio de la última transacción completada


    def trade(self):
        nueva=False
        current_price = self.get_current_price()
        s=f"[#] Analisis # {self.analisis}\n"
        self.analisis+=1
        s+=f"[#] OPERACION ACTUAL: {self.current_operation}\n"
        s+=f"[#] GANANCIA ACTUAL: {self.ganancia}\n"
        s+=f"[#] PRECIO BTC-USDT: {current_price}\n"

        ema5,ema15=self.get_indicator()

        
        if self.current_operation == "LONG":
            if ema5 < ema15:
                s+=self.close_operations(current_price)
                nueva=True
            else:
                s+=self.mantener(current_price)
                #============================================
        elif self.current_operation == "SHORT":
            if ema5 > ema15:
                s+=self.close_operations(current_price)
                nueva=True
            else:
                s+=self.mantener(current_price)
                #============================================

                
        if self.current_operation == None:
            if ema5 > ema15:
                s+=self.open_long(current_price)
                nueva=True
            elif ema5 < ema15:
                s+=self.open_short(current_price)
                nueva=True
            else:
                s+=self.mantener(current_price)
                #============================================
        s+=f"[#] EMA 5: {ema5}\n"
        s+=f"[#] EMA 15: {ema15}\n"
        s+="\n--------------------------------------\n"
        if nueva == True:
            enviar_correo(s)
        return s

    def mantener(self,current_price):
        s=""
        if self.current_operation != None:
            s+=f">>>> MANTENER OPERACION {self.current_operation} a {self.open_price}\n"
            s+="[#] ESTADO: "
            if self.current_operation == "LONG":
                s+=str(current_price-self.open_price)+"\n"
            else:
                s+=str(self.open_price-current_price)+"\n"
        else:
            s+=">>>> NO EJECUTAR ACCION\n"
        return s



    def open_long(self,current_price):
        s=""
        s+=f">>>> ABRIENDO POSICION LONG A {current_price}\n"
        self.current_operation="LONG"
        self.open_price=current_price
        self.save_state()
        return s

    def open_short(self,current_price):
        s=""
        s+=f">>>> ABRIENDO POSICION SHORT A {current_price}\n"
        self.current_operation="SHORT"
        self.open_price=current_price
        self.save_state()
        return s

    def close_operations(self,current_price):
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
        
        bot = SwingTradingBot()
    
    # Iniciar el bot
    while True:
        try:
            print("\nPROCESANDO ANALISIS...")
            s=bot.trade()
            clear_console()
            print(s)
        except Exception as e:
            clear_console()
            print(f"Error: {str(e)}\n")
        print("Esperando para el próximo análisis...")
        tiempo_espera=10

        for i in range(tiempo_espera, 0, -1):
            sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
        sys.stdout.flush()
            
if __name__ == "__main__":
    run_bot()