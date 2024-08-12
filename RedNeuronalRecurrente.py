import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM

import config
class RNN():
    def __init__(self):
        self.model = Sequential()
        self.model.add(LSTM(50, return_sequences=True, input_shape=(config.time_step, 6)))
        '''
            LSTM(50): Añade una capa LSTM con 50 unidades (neuronas).
            return_sequences=True: Indica que la capa LSTM debe devolver la secuencia completa de salida en 
                lugar de solo el último valor. Esto es útil cuando se tienen múltiples capas LSTM.
            input_shape=(time_step, X_train.shape[2]): Define la forma de entrada de los datos. 
                time_step es el número de pasos de tiempo (ventana de tiempo) y X_train.shape[2] es el número de características (en este caso, 5: open, high, low, close, volume)
        '''
        self.model.add(LSTM(50, return_sequences=False))
        '''
            LSTM(50): Añade otra capa LSTM con 50 unidades.
            return_sequences=False: Indica que esta capa LSTM debe devolver solo 
                el último valor de la secuencia, no la secuencia completa.
        '''
        self.model.add(Dense(25))
        '''
            Dense(25): Añade una capa densa con 25 neuronas. Esta capa toma la salida de la última 
                capa LSTM y la procesa.
        '''
        self.model.add(Dense(1))
        '''
            Dense(1): Añade una capa densa con una sola neurona. Esta es la capa de 
            salida que predice el precio de cierre.
        '''
        self.model.compile(optimizer='adam', loss='mean_squared_error')
        '''
            optimizer=‘adam’: Utiliza el optimizador Adam, que es un método de optimización eficiente y 
                ampliamente utilizado.
            loss=‘mean_squared_error’: Define la función de pérdida como el error cuadrático medio (MSE),
                que es adecuado para problemas de regresión.
        '''
    
    def train(self,X_train,y_train):
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        self.model.fit(X_train, y_train, batch_size=config.batch_size, epochs=config.epochs)


    def prediccion(self,X_test,y_test,y_no_scaled,evalua=True):
        X_test=np.array(X_test)
        y_test=np.array(y_test)
        predictions = self.model.predict(X_test)
        scaler = MinMaxScaler()
        y_no_scaled=np.array(y_no_scaled).reshape(-1, 1)
        scaler.fit(y_no_scaled)
        predictions=predictions.reshape(-1, 1)
        predictions = scaler.inverse_transform(predictions)
        loss=None
        if y_test is not None and evalua==True:
            loss = self.model.evaluate(X_test, y_test, verbose=0)
        return predictions,loss
    


    @staticmethod
    def process_data(features):
        # Normaliza los datos
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(features)
        return scaled_data
    

    
    @staticmethod
    def train_test_split(dataset,no_scaled_data,porciento_train):
        dataX, dataY,y_no_scaled = [], [], []
        for i in range(len(dataset)-config.time_step-config.predict_step):
            a = dataset[i:(i+config.time_step), :]
            dataX.append(a)
            dataY.append(dataset[i + config.time_step + config.predict_step - 1, 0])  # Precio de cierre de la última vela en la ventana de predicción
            y_no_scaled.append(no_scaled_data.iloc[i + config.time_step + config.predict_step - 1, 0])
        # Divide los datos en entrenamiento y prueba
        train_size = int(len(dataX) * porciento_train)
        X_train, X_test = dataX[:train_size], dataX[train_size:]
        y_train, y_test = dataY[:train_size], dataY[train_size:]
        y_no_scaled=y_no_scaled[train_size:]
        return X_train,X_test,y_train,y_test,y_no_scaled
    

    @staticmethod
    def get_test_data(dataset):
        dataX = []
        for i in range(len(dataset)-config.time_step-config.predict_step):
            a = dataset[i:(i+config.time_step), :]
            dataX.append(a)
        return dataX