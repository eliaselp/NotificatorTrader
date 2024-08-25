

####CONFIGURACION####
access_id = "2BB2CDB4E9034D5C9EBB04041EBE5089"  # Replace with your access id
secret_key = "CA2792E400D023DAD732CA41C4ED0B98B0CC638FF77D9C65"  # Replace with your secret key
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
