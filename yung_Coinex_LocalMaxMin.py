import pickle
import os
import platform
import sys
import time
import smtplib
import json
import pandas as pd
import numpy as np

from client import RequestsClient
from correo import enviar_correo
import config
# from IPython.display import clear_output

def clear_console():
    os_system = platform.system()
    if os_system == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

# Clase del bot de trading
class SwingTradingBot:
    def __init__(self,apalancamiento):
        #CONFIG
        self.access_id = config.access_id
        self.secret_key = config.secret_key
        self.ENVIO_MAIL= config.ENVIO_MAIL
        self.Operar= config.Operar
        self.email=config.email
        self.simbol=config.simbol
        self.size=config.size
        self.temporalidad=config.temporalidad
        self.ventana=config.ventana

        self.client=RequestsClient(access_id=self.access_id,secret_key=self.secret_key)
        self.apalancamiento=apalancamiento
        self.last_apalancamiento=None
        self.ganancia=0
        self.current_operation=None
        self.current_price=None
        self.id_operation=None
        self.open_price=None
        self.last_rsi=None
        self.analisis=1
        self.cant_opr=0
        self.cant_win=0
        self.cant_loss=0
        self.save_state()

    
    #LISTO
    def get_data(self):
        request_path = "/futures/kline"
        params = {
            "market":self.simbol,
            "limit":self.size,
            "period":self.temporalidad
        }
        response = self.client.request(
            "GET",
            "{url}{request_path}".format(url=self.client.url, request_path=request_path),
            params=params,
        )
        data=response.json().get("data")
        ohlcv_df = pd.DataFrame(data)
        # Convertir las columnas de precios y volumen a numérico
        ohlcv_df['close'] = pd.to_numeric(ohlcv_df['close'])
        ohlcv_df['high'] = pd.to_numeric(ohlcv_df['high'])
        ohlcv_df['low'] = pd.to_numeric(ohlcv_df['low'])
        ohlcv_df['open'] = pd.to_numeric(ohlcv_df['open'])
        ohlcv_df['volume'] = pd.to_numeric(ohlcv_df['volume'])
        self.current_price = ohlcv_df['close'].iloc[-1]
        if config.incluir_precio_actual==False:
            ohlcv_df = ohlcv_df.drop(ohlcv_df.index[-1])
        return ohlcv_df


    def calculate_sma(self, periods):
        ohlcv_df = self.get_data()
        sma_values = {}
        for period in periods:
            sma_values[f'SMA_{period}'] = ohlcv_df['close'].rolling(window=period).mean().iloc[-1]
        return sma_values
    
    def identificar_tendencia(self):
        sma=self.calculate_sma([5,20,25])
        if sma['SMA_5'] > sma['SMA_20'] and sma['SMA_20'] > sma['SMA_25']:
            return 'compra',sma
        if sma['SMA_5'] < sma['SMA_20'] and sma['SMA_20'] < sma['SMA_25']:
            return 'venta',sma
        return 'lateralizacion',sma




    def identificar_patron(self):
        ohlcv_df=self.get_data()
        # Encontrar máximos y mínimos locales
        # Asegurarse de que la ventana rodante tenga exactamente 5 elementos antes de aplicar la función lambda
        maximos = ohlcv_df['high'].rolling(window=5, center=False).apply(
            lambda x: x[self.ventana//2] if (len(x) == self.ventana and x[self.ventana//2] == x.max()) else np.nan, raw=True
        )
        minimos = ohlcv_df['low'].rolling(window=5, center=False).apply(
            lambda x: x[self.ventana//2] if (len(x) == self.ventana and x[self.ventana//2] == x.min()) else np.nan, raw=True
        )
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


    
    
    #ESTRATEGIA LISTA
    def trade(self):
        patron=''
        sma=None
        if config.estrategia==1:
            patron=self.identificar_patron()
        elif config.estrategia==2:
            patron,sma=self.identificar_tendencia()

        nueva=False
        s=f"[#] Analisis # {self.analisis}\n"
        self.analisis+=1
        s+=f"[#] OPERACION ACTUAL: {self.current_operation}\n"
        s+=f"[#] GANANCIA ACTUAL: {self.ganancia}\n"
        s+=f"[#] PRECIO BTC-USDT: {self.current_price}\n"
        s+=f"[#] PATRON: {patron}\n"
        balance=7
        if self.current_operation == "LONG":
            if patron in ["venta","lateralizacion"]:
                s+=self.close_operations(self.current_price)
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================
        elif self.current_operation == "SHORT":
            if patron in ["compra","lateralizacion"]:
                s+=self.close_operations(self.current_price)
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================

                
        if self.current_operation == None:
            if patron=="compra" and balance*0.9>=2:
                s+=self.open_long()
                nueva=True
            elif patron=="venta" and balance*0.9>=2:
                s+=self.open_short()
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================
        if sma:
            sma=dict(sorted(sma.items(), key=lambda item: item[1], reverse=True))
            s+=str(pd.DataFrame([sma]))+"\n"
        s+=f"[#] BALANCE: {balance} USDT\n"
        s+=f"[#] OPERACIONES: {self.cant_opr}\n"
        s+=f"[#] GANADAS: {self.cant_win}\n"
        s+=f"[#] PERDIDAS: {self.cant_loss}\n"
        s+="\n--------------------------------------\n"
        if nueva == True and self.ENVIO_MAIL==True:
            enviar_correo(s=s,email=self.email)
        return s


    def close_operations(self,current_price):
        if self.Operar:
            self.close()
        s=""
        s+=f"[++++] CERRANDO POSICION {self.current_operation}\n"
        if self.current_operation == "LONG":
            self.ganancia+=current_price - self.open_price
            s+=f"[#] ESTADO: {current_price - self.open_price}\n"
            if current_price - self.open_price > 0:
                self.cant_win+=1
            else:
                self.cant_loss+=1
        else:
            self.ganancia+=self.open_price - current_price
            s+=f"[#] ESTADO: {self.open_price - current_price}\n"
            if self.open_price - current_price > 0:
                self.cant_win+=1
            else:
                self.cant_loss+=1
        s+=f"[#] GANANCIA: {self.ganancia}\n"
        self.open_price=None
        self.current_operation=None
        self.save_state()
        return s

    #LISTO
    def mantener(self,current_price,s=""):
        s=""
        if self.current_operation != None:
            s+=f"[++++] MANTENER OPERACION {self.current_operation} a {self.open_price}\n"
            s+="[#] ESTADO: "
            if self.current_operation == "LONG":
                s+=str(current_price-self.open_price)+"\n"
            else:
                s+=str(self.open_price-current_price)+"\n"
        else:
            s+="[#] NO EJECUTAR ACCION\n"
        return s

    #LISTO
    def open_long(self,s=""):
        self.open_price=self.current_price
        s=""
        if self.open_price == None:
            s+=f"[++++] Error al abrir posicion en long:\n"
        else:
            s+=f"[++++] ABRIENDO POSICION LONG A {self.open_price}\n"
            self.current_operation="LONG"
            self.cant_opr+=1
            self.save_state()
        return s

    #LISTO
    def open_short(self,s=""):
        self.open_price=self.current_price
        s=""
        if self.open_price == None:
            s+=f"[++++] Error al abrir posicion en short:\n"
        else:
            s+=f"[++++] ABRIENDO POSICION SHORT A {self.open_price}\n"
            self.current_operation="SHORT"
            self.cant_opr+=1
            self.save_state()
        return s

    #LISTO
    def save_state(self):
        with open('bot_state_yung2_0.pkl', 'wb') as file:
            pickle.dump(self, file)

    #LISTO
    @staticmethod
    def load_state():
        if os.path.exists('bot_state_yung2_0.pkl'):
            with open('bot_state_yung2_0.pkl', 'rb') as file:
                return pickle.load(file)
        else:
            return None


def run_bot():
    # Intentar recuperar el estado del bot
    print("[#] Seleccione nivel de apalancamiento: ")
    print("[0] 1x")
    print("[1] 10x")
    print("[2] 20x")
    print("[3] 30x")
    print("[4] 40x")
    print("[5] 50x")
    print("[6] 60x")
    print("[7] 70x")
    print("[8] 80x")
    print("[9] 90x")
    print("[10] 100x")
    opc=int(input('==>>> '))
    apalancamiento=1
    if opc==1:
        apalancamiento=10
    elif opc==2:
        apalancamiento=20
    elif opc==3:
        apalancamiento=30
    elif opc==4:
        apalancamiento=40
    elif opc==5:
        apalancamiento=50
    elif opc==6:
        apalancamiento=60
    elif opc==7:
        apalancamiento=70
    elif opc==8:
        apalancamiento=80
    elif opc==9:
        apalancamiento=90
    elif opc==10:
        apalancamiento=100

    bot = SwingTradingBot.load_state()
    if bot is None:
        bot = SwingTradingBot(apalancamiento)
    else:
        bot.apalancamiento=apalancamiento
        bot.access_id = config.access_id
        bot.secret_key = config.secret_key
        bot.ENVIO_MAIL= config.ENVIO_MAIL
        bot.Operar= config.Operar
        bot.email=config.email
        bot.simbol=config.simbol
        bot.size=config.size
        bot.temporalidad=config.temporalidad
        bot.ventana=config.ventana
        bot.save_state()

    clear_console()
    
    # Iniciar el bot
    while True:
        error=False
        try:
            print("\nPROCESANDO ANALISIS...")
            s=bot.trade()
            clear_console()
            print(s)
        except Exception as e:
            clear_console()
            print(f"Error: {str(e)}\n")
            error=True
        print("Esperando para el próximo análisis...")
        if error:
            tiempo_espera=1
        else:
            tiempo_espera=config.tiempo_espera
        for i in range(tiempo_espera, 0, -1):
            sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
        sys.stdout.flush()
