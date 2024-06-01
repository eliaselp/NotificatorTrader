import os
import platform
import sys
import time
import pickle
import json

import pandas as pd
import numpy as np

from client import RequestsClient
import correo
'''

import requests
import hashlib
import hmac
from urllib.parse import urlencode
from hashlib import sha256


'''

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
        access_id = "2BB2CDB4E9034D5C9EBB04041EBE5089"  # Replace with your access id
        secret_key = "CA2792E400D023DAD732CA41C4ED0B98B0CC638FF77D9C65"  # Replace with your secret key
        self.ENVIO_MAIL=True
        self.Operar=False
        self.delete_fast=False
        self.simbol="BTCUSDT"
        self.email="liranzaelias@gmail.com"

        self.client=RequestsClient(access_id=access_id,secret_key=secret_key)
        self.apalancamiento=apalancamiento
        self.ganancia=0
        self.current_price=None
        self.current_operation=None
        self.id_operation=None
        self.open_price=None
        self.analisis=1

        self.cant_opr=0
        self.cant_opr_win=0
        self.cant_opr_over=0

        self.save_state()


    

    def get_balance(self):
        pass


     #LISTO
    def get_balance(self):
        pass    

    
    #LISTO
    def set_apalancamiento(self,modo):
        pass

    def open(self,tipo):
        pass
    



    

    #LISTO
    def get_data(self,size,temporalidad):
        request_path = "/futures/kline"
        params = {
            "market":self.simbol,
            "limit":size,
            "period":temporalidad
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
        return ohlcv_df


    #ESTRATEGIA LISTA
    def trade(self):
        data=self.get_data(500,"4hour")
        patron=self.identificar_patron(data)
        balance=7
        s=""
        nueva=False
        if self.current_operation == "LONG":
            if patron in ["venta","lateralizacion"]:
                s+=self.close_operations(self.current_price)
                nueva=True
            else:
                s+=self.mantener(self.current_price)
        elif self.current_operation == "SHORT":
            if (patron in ["compra","lateralizacion"]):
                s+=self.close_operations(self.current_price)
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================

                
        if self.current_operation == None:
            if patron=="compra" and balance*0.9>=2:
                self.set_apalancamiento("LONG")
                s+=self.open_long()
                nueva=True
            elif patron=="venta" and balance*0.9>=2:
                self.set_apalancamiento("SHORT")
                s+=self.open_short()
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================
        
        s=f"[#] Analisis # {self.analisis}\n"
        self.analisis+=1
        s+=f"[#] OPERACION ACTUAL: {self.current_operation}\n"
        s+=f"[#] GANANCIA ACTUAL: {self.ganancia}\n"
        s+=f"[#] PRECIO BTC-USDT: {self.current_price}\n"
        s+=f"[#] OPERACIONES: {self.cant_opr}\n"
        s+=f"[#] GANADAS: {self.cant_opr_win}\n"
        s+=f"[#] PERDIDAS: {self.cant_opr_over}\n"        
        s+=f"SEÑAL: {patron}\n"
        s+=f"[#] BALANCE: {balance} USDT\n"
        s+="\n--------------------------------------\n"
        if nueva == True and self.ENVIO_MAIL==True:
            correo.enviar_correo(s,self.email)
        return s


    def identificar_patron(self,ohlcv_df):
        # Encontrar máximos y mínimos locales
        # Asegurarse de que la ventana rodante tenga exactamente 5 elementos antes de aplicar la función lambda
        maximos = ohlcv_df['high'].rolling(window=5, center=False).apply(
            lambda x: x[2] if (len(x) == 5 and x[2] == x.max()) else np.nan, raw=True
        )
        minimos = ohlcv_df['low'].rolling(window=5, center=False).apply(
            lambda x: x[2] if (len(x) == 5 and x[2] == x.min()) else np.nan, raw=True
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


    def close_operations(self,current_price):
        if self.Operar:
            self.close()
        self.cant_opr+=1
        s=""
        s+=f">>>> CERRANDO POSICION {self.current_operation}\n"
        estado=0
        if self.current_operation == "LONG":
            estado=current_price - self.open_price
            self.ganancia+=estado
            s+=f"[#] ESTADO: {estado}\n"
        else:
            estado=self.open_price - current_price
            self.ganancia+=estado
            s+=f"[#] ESTADO: {estado}\n"
        s+=f"[#] GANANCIA: {self.ganancia}\n"
        if estado>0:
            self.cant_opr_win+=1
        else:
            self.cant_opr_over+=1
        self.open_price=None
        self.current_operation=None
        self.save_state()
        return s

    #LISTO
    def mantener(self,current_price,s=""):
        s=""
        if self.current_operation != None:
            s+=f">>>> MANTENER OPERACION {self.current_operation} a {self.open_price}\n"
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
        if self.Operar:
            self.open("LONG")
        self.open_price=self.current_price
        s=""
        if self.open_price == None:
            s+=f">>>> Error al abrir posicion en long:\n"
        else:
            s+=f">>>> ABRIENDO POSICION LONG A {self.open_price}\n"
            self.current_operation="LONG"
            self.save_state()
        return s

    #LISTO
    def open_short(self,s=""):
        if self.Operar:
            self.open("SHORT")
        self.open_price=self.current_price
        s=""
        if self.open_price == None:
            s+=f">>>> Error al abrir posicion en short:\n"
        else:
            s+=f">>>> ABRIENDO POSICION SHORT A {self.open_price}\n"
            self.current_operation="SHORT"
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
        bot.set_apalancamiento("LONG")
        bot.set_apalancamiento("SHORT")
    clear_console()
    
    # Iniciar el bot
    while True:
        error=False
        #try:
        print("\nPROCESANDO ANALISIS...")
        s=bot.trade()
        clear_console()
        print(s)
        #except Exception as e:
        #    clear_console()
        #    print(f"Error: {str(e)}\n")
        #    error=True
        print("Esperando para el próximo análisis...")
        if error:
            tiempo_espera=1
        else:
            tiempo_espera=1
        for i in range(tiempo_espera, 0, -1):
            sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
        sys.stdout.flush()
    
if __name__ == "__main__":
    run_bot()
