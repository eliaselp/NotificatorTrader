import pickle
import os
import platform
import sys
import time
import pandas as pd
import numpy as np
import pandas_ta as ta

from client import RequestsClient
from RedNeuronalRecurrente import RNN
from correo import enviar_correo
from monitor import update_text_code,post_action
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
    def __init__(self):
        self.nuevo = True
        self.last_data=None#Esto es para que controlar el momento de entrenamiento del modelo        
        self.ganancia=0
        self.current_operation=None
        self.current_price=None
        self.open_price=None
        self.last_patron=None
        self.analisis=1
        self.cant_opr=0
        self.cant_win=0
        self.cant_loss=0
        self.client=RequestsClient(access_id=config.access_id,secret_key=config.secret_key)

        self.modelo=RNN()
        self.error_cuadratico_medio=None
        self.last_prediccion=None
        self.last_loss=None
        self.save_state()


    def predecir(self, data):
        if str(data)!=self.last_data:
            if self.analisis % config.reset_model == 0:
                self.modelo=RNN()

            self.last_data=str(data)
            if self.nuevo == False:
                data = data.iloc[data.shape[0]-config.time_step-config.predict_step-3:,:]
            else:
                self.nuevo = False
            scaled_data=RNN.process_data(data)
            X_train,X_test,y_train,y_test,y_no_scaled=RNN.train_test_split(scaled_data,data,porciento_train=0.8)
            self.modelo.train(X_train=X_train,y_train=y_train)
            predictions,loss=self.modelo.prediccion(X_test=X_test,y_test=y_test,y_no_scaled=y_no_scaled)
            #---------------------------------------------------------------
            X_test=self.modelo.get_test_data(scaled_data[-config.time_step-config.predict_step-1:,:])
            predictions,loss2=self.modelo.prediccion(X_test=X_test,y_test=data,y_no_scaled=data.iloc[-config.time_step-config.predict_step-1:,0],evalua=False)
            
            self.last_prediccion=predictions[0, 0]
            self.last_loss=loss
            predictions=predictions[0, 0]
            
            if predictions > data.iloc[-1,0]:
                self.last_patron="LONG"
                return "LONG",loss,predictions
            elif predictions < data.iloc[-1,0]:
                self.last_patron="SHORT"
                return "SHORT",loss,predictions
            else:
                self.last_patron="Lateralizacion"
                return "Lateralizacion",loss,predictions
        else:
            return self.last_patron,self.last_loss,self.last_prediccion


    #ESTRATEGIA LISTA
    def trade(self):
        patron=''
        sma=None
        s=""

        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        #generar_señal
        data=self.get_data()
        patron,loss,prediction=self.predecir(data)
        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

        nueva=False
        s=f"[#] Analisis # {self.analisis}\n"
        self.analisis+=1
        s+=f"[#] OPERACION ACTUAL: {self.current_operation}\n"
        s+=f"[#] GANANCIA ACTUAL: {self.ganancia}\n"
        s+=f"[#] PRECIO BTC-USDT: {self.current_price}\n"
        s+=f"[###] PREDICCION: {prediction}\n"
        s+=f"[#] ERROR CUADRATICO MEDIO: {loss}\n"
        s+=f"[#] PATRON: {patron}\n"

        balance=7

        if self.current_operation == "LONG":
            if patron in ["SHORT","Lateralizacion"]:
                s+=self.close_operations(self.current_price)
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================
        elif self.current_operation == "SHORT":
            if patron in ["LONG","Lateralizacion"]:
                s+=self.close_operations(self.current_price)
                nueva=True
            else:
                s+=self.mantener(self.current_price)
                #============================================

                
        if self.current_operation == None:
            if patron=="LONG" and balance*0.9>=2:
                s+=self.open_long()
                nueva=True
            elif patron=="SHORT" and balance*0.9>=2:
                s+=self.open_short()
                nueva=True
            else:
                s+=self.mantener(self.current_price)

        s+=f"[#] BALANCE: {balance} USDT\n"
        s+=f"[#] OPERACIONES: {self.cant_opr}\n"
        s+=f"[#] GANADAS: {self.cant_win}\n"
        s+=f"[#] PERDIDAS: {self.cant_loss}\n"
        s+="\n--------------------------------------\n"
        if nueva == True and config.ENVIO_MAIL==True:
            enviar_correo(s=s,email=config.email)
        return s

    def close_operations(self,current_price):
        if config.Operar:
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
        
        post_action(self.ganancia,self.analisis)
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
    def get_data(self):
        request_path = "/futures/kline"
        params = {
            "market":config.simbol,
            "limit":config.size,
            "period":config.temporalidad
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
        ohlcv_df = ohlcv_df.drop('market', axis=1)
        ohlcv_df = ohlcv_df.drop('created_at', axis=1)
        if config.incluir_precio_actual==False:
            ohlcv_df = ohlcv_df.drop(ohlcv_df.index[-1])
        ohlcv_df['RSI'] = ta.rsi(ohlcv_df['close'],length=15)
        ohlcv_df['EMAF'] = ta.ema(ohlcv_df['close'],length=7)
        ohlcv_df['EMAM'] = ta.ema(ohlcv_df['close'],length=50)
        ohlcv_df['EMAS'] = ta.ema(ohlcv_df['close'],length=100)
        ohlcv_df = ohlcv_df.iloc[100:,:]
        
        '''
        ohlcv_df = ta.add_all_ta_features(
            ohlcv_df, open="open", high="high", low="low", close="close", volume="volume", fillna=True
        )
        '''
        return ohlcv_df


    #LISTO
    def save_state(self):
        with open('yungIA_data.pkl', 'wb') as file:
            pickle.dump(self, file)

    #LISTO
    @staticmethod
    def load_state():
        if os.path.exists('yungIA_data.pkl'):
            with open('yungIA_data.pkl', 'rb') as file:
                return pickle.load(file)
        else:
            return None


def run_bot():
    bot = SwingTradingBot.load_state()
    if bot is None:
        bot = SwingTradingBot()

    clear_console()
    
    # Iniciar el bot
    while True:
        error=False
        try:
            print("\nPROCESANDO ANALISIS...")
            s=bot.trade()
            clear_console()
            update_text_code(mensaje=s)
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
