

####CONFIGURACION####
access_id = "CA67B0440BB547499F0BF8A632741AF0"  # Replace with your access id
secret_key = "5BBFB51795FDCFB32777F34F113720EC9C2598905DBD679F"  # Replace with your secret key
simbol="BTCUSDT"

ENVIO_MAIL=True
email="liranzaelias@gmail.com"
Operar=False

url_base = "https://monitoreo.pythonanywhere.com/"
#url_base = "http://localhost:8000/"

incluir_precio_actual=False


size=1000
temporalidad="1hour"
tiempo_espera=5 #segundos


#CONFIG RED NEURONAL RECURRENTE
batch_size=1
epochs=5

time_step=500
predict_step=5

reset_model = 0
