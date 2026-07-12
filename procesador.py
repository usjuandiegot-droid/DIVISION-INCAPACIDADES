import pandas as pd
import time


def dividir_incapacidades_por_mes(row):
    """
    Divide una incapacidad en varios registros cuando abarca más de un mes.
    """

    fechas = []

    inicio = row["Fecha de Inicio"]
    fin = row["Fecha de Fin"]

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

    inicio = time.time()

    print("1. Leyendo Excel...", flush=True)

    df = pd.read_excel(archivo_entrada)

    print("2. Excel leído", flush=True)

    print("3. Convirtiendo fechas...", flush=True)

    df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"])
    df["Fecha de Fin"] = pd.to_datetime(df["Fecha de Fin"])

    print("4. Dividiendo por meses...", flush=True)

    df["meses"] = df.apply(dividir_incapacidades_por_mes, axis=1)

    print("5. Explode...", flush=True)

    resultados = df.explode("meses")

    print("6. Convirtiendo columnas...", flush=True)

    resultados = pd.concat(
        [
            resultados.drop(columns=["meses"]),
            resultados["meses"].apply(pd.Series)
        ],
        axis=1
    )

    if "Dias Pagados" in resultados.columns:
        resultados = resultados.drop(columns=["Dias Pagados"])

    print("7. Guardando Excel...", flush=True)

    with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
        resultados.to_excel(
            writer,
            index=False,
            sheet_name="Base HMV"
        )

    print(f"8. Finalizado en {time.time() - inicio:.2f} segundos", flush=True)

def procesar_peru(archivo_entrada, archivo_salida):
    shutil.copy(archivo_entrada, archivo_salida)
