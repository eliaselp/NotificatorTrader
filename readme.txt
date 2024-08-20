En esta version hay una red neuronal recurrente.
Esta red neuronal hace predicciones en el precio a n velas en el futuro segun dice la configuracion.

en esta version SI se hace verificacion de medias moviles Y se calculan indicadores tecnicos.



conectarme por ssh a mi servidor
ssh -i "ADMIN.pem" ubuntu@ec2-3-22-101-173.us-east-2.compute.amazonaws.com


ejecutar en segundo plano
nohup python run.py > output.log 2>&1 &


revisar el proceso
ps aux | grep run.py


matar el proceso
kill <PID>




