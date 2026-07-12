import pandas as pd
import time

inicio = time.time()
print("1. Leyendo Excel...")

def dividir_incapacidades_por_mes(row):
    """
    Divide una incapacidad en varios registros cuando abarca más de un mes.
    """
    print("2. Excel leído")
    print("3. Convirtiendo fechas...")
    fechas = []

    inicio = row["Fecha de Inicio"]
    fin = row["Fecha de Fin"]
    print("4. Dividiendo por meses...")
    while inicio <= fin:

        mes = inicio.month
        anio = inicio.year

        ultimo_dia_mes = (
            pd.Timestamp(anio, mes, 1)
            + pd.DateOffset(months=1)
            - pd.DateOffset(days=1)
        )

        if fin < ultimo_dia_mes:
            ultimo_dia_mes = fin

        dias_mes = (ultimo_dia_mes - inicio).days + 1

        fechas.append({
            "Mes": pd.Timestamp(anio, mes, 1),
            "Total Días": dias_mes
        })

        inicio = ultimo_dia_mes + pd.DateOffset(days=1)

    return fechas


def procesar_colombia(archivo_entrada, archivo_salida):

    # Leer archivo
    df = pd.read_excel(archivo_entrada)

    # Convertir fechas
    df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"])
    df["Fecha de Fin"] = pd.to_datetime(df["Fecha de Fin"])

    # Dividir incapacidades por mes
    df["meses"] = df.apply(dividir_incapacidades_por_mes, axis=1)

    # Expandir las listas en filas
    resultados = df.explode("meses")
    print("5. Explode terminado")
    # Crear columnas Mes y Total Días
    resultados = pd.concat(
        [
            resultados.drop(columns=["meses"]),
            resultados["meses"].apply(pd.Series)
        ],
        axis=1
    )

    # Eliminar columna si existe
    if "Dias Pagados" in resultados.columns:
        resultados = resultados.drop(columns=["Dias Pagados"])
    
    print("6. Guardando Excel...")

    # Guardar resultado
    with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
        resultados.to_excel(
            writer,
            index=False,
            sheet_name="Base HMV"
        )

    print(f"7. Finalizado en {time.time()-inicio:.2f} segundos")


def procesar_peru(archivo_entrada, archivo_salida):
    shutil.copy(archivo_entrada, archivo_salida)
