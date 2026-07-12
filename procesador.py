import pandas as pd


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

    # Leer archivo
    df = pd.read_excel(archivo_entrada)

    # Convertir fechas
    df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"])
    df["Fecha de Fin"] = pd.to_datetime(df["Fecha de Fin"])

    # Dividir incapacidades por mes
    df["meses"] = df.apply(dividir_incapacidades_por_mes, axis=1)

    # Expandir las listas en filas
    resultados = df.explode("meses")

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

    # Guardar resultado
    with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
        resultados.to_excel(
            writer,
            index=False,
            sheet_name="Base HMV"
        )




def procesar_peru(archivo_entrada, archivo_salida):
    shutil.copy(archivo_entrada, archivo_salida)
