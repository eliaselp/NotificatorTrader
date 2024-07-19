import pandas as pd

def eliminar_ultimas_filas(df, num_filas=5):
    # Elimina las últimas 'num_filas' filas del DataFrame
    df.drop(df.index[-num_filas:], inplace=True)

data = {
    "nombre_producto": ["Teclado", "Ratón", "Monitor", "CPU", "Altavoces"],
    "precio_unitario": [500, 200, 5000.235, 10000.550, 250.50]
}

df = pd.DataFrame(data)

print(df)  # Imprime el DataFrame resultante
# Elimina las últimas 5 filas
eliminar_ultimas_filas(df, num_filas=5)

print(df)  # Imprime el DataFrame resultante