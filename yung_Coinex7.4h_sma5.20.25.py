import os
import platform
import sys
import time
import pickle
import pandas as pd


from client import RequestsClient
from . import correo
'''

import requests
import hashlib
import hmac
from urllib.parse import urlencode
from hashlib import sha256
import json

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
        self.current_operation=None
        self.id_operation=None
        self.open_price=None
        self.analisis=1
        self.save_state()


    def get_current_price(self):
        pass

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
        return response


    def get_indicator(self):
        '''
        Período de velas.
        Uno de ["1min", "3min", "5min", "15min", "30min", "1hour", "2hour", "4hour", "6hour", 
        "12hour", "1day", "3day", "1week"]
        '''
        precios_cierre = self.get_data(30,"4hour")
        while precios_cierre.__len__()==0:
            print("[#] reobteniendo los datos historicos....")
            precios_cierre = self.get_data(30,"4h")
        precios_cierre = [float(precio) for precio in precios_cierre]
        current_price=float(precios_cierre[0])
        precios_cierre
        if self.delete_fast:
            precios_cierre.pop(0)
        
        precios_cierre=precios_cierre[::-1]
        

        df = pd.DataFrame(precios_cierre, columns=['close'])
        df['ema25'] = df['close'].ewm(span=25).mean()
        df['ema5'] = df['close'].ewm(span=5).mean()
        df['ema20'] = df['close'].ewm(span=20).mean()
        # Devolverlos últimos valores de las EMAs como variables separadas
        ema5 = df['ema5'].iloc[-1]
        ema20 = df['ema20'].iloc[-1]
        ema25 = df['ema25'].iloc[-1]
        
        balance = self.get_balance()
        while balance == None:
            print("[#] reobteniendo el balance....")
            balance = self.get_balance()
         # Devolver los valores calculados
        return ema5,ema20,ema25,balance,current_price
    
   
    #ESTRATEGIA LISTA
    def trade(self):
        ema5,ema20,ema25,balance,current_price=self.get_indicator()
        self.current_price=current_price
        nueva=False
        s=f"[#] Analisis # {self.analisis}\n"
        self.analisis+=1
        s+=f"[#] OPERACION ACTUAL: {self.current_operation}\n"
        s+=f"[#] GANANCIA ACTUAL: {self.ganancia}\n"
        s+=f"[#] PRECIO BTC-USDT: {current_price}\n"

        
        if self.current_operation == "LONG":
            if (ema5<ema20):
                s+=self.close_operations(current_price)
                nueva=True
            else:
                s+=self.mantener(current_price)
                #============================================
        elif self.current_operation == "SHORT":
            if (ema5>ema20):
                s+=self.close_operations(current_price)
                nueva=True
            else:
                s+=self.mantener(current_price)
                #============================================

                
        if self.current_operation == None:
            if (ema5>ema20 and ema20>ema25) and current_price>ema25 and balance*0.9>=2:
                self.set_apalancamiento("LONG")
                s+=self.open_long()
                nueva=True
            elif (ema5<ema20 and ema20<ema25) and current_price<ema25 and balance*0.9>=2:
                self.set_apalancamiento("SHORT")
                s+=self.open_short()
                nueva=True
            else:
                s+=self.mantener(current_price)
                #============================================
        emas={
            "[#] EMA 5: ":ema5,
            "[#] EMA 20: ":ema20,
            "[#] EMA 25: ":ema25,
        }   
        emas=dict(sorted(emas.items(), key=lambda item: item[1], reverse=True))
        for clave,valor in emas.items():
            s+=clave
            s+=f"{valor}\n"
        
        s+=f"[#] BALANCE: {balance} USDT\n"
        s+="\n--------------------------------------\n"
        if nueva == True and self.ENVIO_MAIL==True:
            correo.enviar_correo(s,self.email)
        return s


    def close_operations(self,current_price):
        if self.Operar:
            self.close()
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
            tiempo_espera=1
        for i in range(tiempo_espera, 0, -1):
            sys.stdout.write("\rTiempo restante: {:02d}:{:02d} ".format(i // 60, i % 60))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\r" + " " * 50)  # Limpiar la línea después de la cuenta regresiva
        sys.stdout.flush()
    
if __name__ == "__main__":
    run_bot()