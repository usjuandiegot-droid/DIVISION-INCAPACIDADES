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

    print(f"Filas y columnas: {resultados.shape}", flush=True)
    
    memoria_mb = resultados.memory_usage(deep=True).sum() / 1024 / 1024
    print(f"Memoria del DataFrame: {memoria_mb:.2f} MB", flush=True)
    
    with pd.ExcelWriter(archivo_salida, engine="xlsxwriter") as writer:
        resultados.to_excel(
            writer,
            index=False,
            sheet_name="Base HMV"
        )

    print(f"8. Finalizado en {time.time() - inicio:.2f} segundos", flush=True)


def aplicar_regla_peru(df):
    df.columns = df.columns.str.strip()  # Elimina espacios en los nombres de las columnas

    # Verificar que las columnas necesarias existen
    columnas_requeridas = ["Documento", "Total de Días", "Fecha de Inicio", "Tipo Incapacidad"]
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(f"No se encontró la columna '{col}' en el archivo.")

    # Convertir la columna de fecha al formato datetime
    df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"], errors='coerce')

    # Ordenar por documento y fecha para calcular correctamente la acumulación de días
    df = df.sort_values(by=["Documento", "Fecha de Inicio"]).reset_index(drop=True)

    # Diccionario para almacenar días acumulados por documento en cada año
    dias_acumulados = {}

    # Lista para almacenar los nuevos registros
    nueva_data = []

    # Iterar sobre cada fila del archivo original
    for _, row in df.iterrows():
        documento = row["Documento"]
        dias = row["Total de Días"]
        fecha_inicio = row["Fecha de Inicio"]
        tipo_incapacidad = row["Tipo Incapacidad"].strip().upper()
        anio = fecha_inicio.year  # Extraer el año de la incapacidad

        # Validar que la fecha sea correcta
        if pd.isnull(fecha_inicio):
            raise ValueError(f"La fecha de inicio no es válida en la fila: {row}")

        # Si es Licencia de Maternidad, se registra directamente como Subsidio por Maternidad
        if tipo_incapacidad == "LICENCIA DE MATERNIDAD":
            row_maternidad = row.copy()
            row_maternidad["Tipo"] = "Subsidio por Maternidad"
            row_maternidad["Fecha de Inicio (Tipo)"] = fecha_inicio
            row_maternidad["Fecha de Fin (Tipo)"] = fecha_inicio + pd.Timedelta(days=dias - 1)
            nueva_data.append(row_maternidad)
            continue  # No se acumulan días de maternidad en el conteo anual

        # Inicializar acumulación si es el primer registro del documento en ese año
        if documento not in dias_acumulados:
            dias_acumulados[documento] = {}

        if anio not in dias_acumulados[documento]:
            dias_acumulados[documento][anio] = 0  # Reinicia el conteo de días para el nuevo año

        # Contar solo los días en el año actual
        dias_previos = dias_acumulados[documento][anio]

        # Crear una copia de la fila original
        row_descanso = row.copy()
        row_descanso["Fecha de Inicio (Tipo)"] = fecha_inicio

        # Si aún no ha acumulado 20 días en el año, darle Descanso Médico primero
        if dias_previos < 20:
            dias_descanso = min(20 - dias_previos, dias)
            row_descanso["Total de Días"] = dias_descanso
            row_descanso["Tipo"] = "Descanso Médico"
            row_descanso["Fecha de Fin (Tipo)"] = fecha_inicio + pd.Timedelta(days=dias_descanso - 1)
            nueva_data.append(row_descanso)

            # Actualizar los días acumulados
            dias_acumulados[documento][anio] += dias_descanso
            dias -= dias_descanso
            fecha_inicio = row_descanso["Fecha de Fin (Tipo)"] + pd.Timedelta(days=1)

        # Si quedan días pendientes, esos ya son Subsidio
        if dias > 0:
            row_subsidio = row.copy()
            row_subsidio["Total de Días"] = dias
            row_subsidio["Tipo"] = "Subsidio por Incapacidad Temporal"
            row_subsidio["Fecha de Inicio (Tipo)"] = fecha_inicio
            row_subsidio["Fecha de Fin (Tipo)"] = fecha_inicio + pd.Timedelta(days=dias - 1)
            nueva_data.append(row_subsidio)

            # Actualizar los días acumulados
            dias_acumulados[documento][anio] += dias

    # Crear nuevo DataFrame con las filas divididas
    df_nuevo = pd.DataFrame(nueva_data)
   
    return df_nuevo

def procesar_peru(archivo_entrada, archivo_salida):

    import time

    inicio = time.time()

    print("1. Leyendo Excel Perú...", flush=True)

    # Leer archivo
    df = pd.read_excel(archivo_entrada, usecols=range(17))

    print("2. Excel leído", flush=True)

    print("3. Aplicando regla de los 20 días...", flush=True)

    # Aplicar la regla de Perú
    df = aplicar_regla_peru(df)

    print(f"Registros después de aplicar la regla: {df.shape}", flush=True)

    print("4. Renombrando columnas...", flush=True)

    # Renombrar temporalmente para reutilizar la función
    df = df.rename(columns={
        "Fecha de Inicio (Tipo)": "Fecha de Inicio",
        "Fecha de Fin (Tipo)": "Fecha de Fin"
    })

    print("5. Convirtiendo fechas...", flush=True)

    # Asegurar formato fecha
    df["Fecha de Inicio"] = pd.to_datetime(df["Fecha de Inicio"])
    df["Fecha de Fin"] = pd.to_datetime(df["Fecha de Fin"])

    print("6. Dividiendo por meses...", flush=True)

    # Dividir por meses
    df["meses"] = df.apply(dividir_incapacidades_por_mes, axis=1)

    print("7. Explode...", flush=True)

    resultados = df.explode("meses")

    print("8. Convirtiendo columnas...", flush=True)

    resultados = pd.concat(
        [
            resultados.drop(columns=["meses"]),
            resultados["meses"].apply(pd.Series)
        ],
        axis=1
    )

    print(f"Filas y columnas: {resultados.shape}", flush=True)

    memoria_mb = resultados.memory_usage(deep=True).sum() / 1024 / 1024
    print(f"Memoria del DataFrame: {memoria_mb:.2f} MB", flush=True)

    print("9. Restaurando nombres de columnas...", flush=True)

    # Renombrar nuevamente las columnas
    resultados = resultados.rename(columns={
        "Fecha de Inicio": "Fecha de Inicio (Tipo)",
        "Fecha de Fin": "Fecha de Fin (Tipo)"
    })

    print("10. Reorganizando columnas...", flush=True)

    # Mover Codigo al final
    if "Codigo" in resultados.columns:
        columnas = [c for c in resultados.columns if c != "Codigo"] + ["Codigo"]
        resultados = resultados[columnas]

        resultados.rename(columns={"Codigo": "ID"}, inplace=True)

    print("11. Agregando Fecha Ingreso...", flush=True)

    # Agregar Fecha Ingreso
    resultados["Fecha Ingreso"] = pd.NaT

    print("12. Eliminando columnas innecesarias...", flush=True)

    # Eliminar columnas
    columnas_a_eliminar = [
        "TIPO",
        "Fecha de Inicio (Tipo)",
        "Fecha de Fin (Tipo)"
    ]

    resultados = resultados.drop(
        columns=[c for c in columnas_a_eliminar if c in resultados.columns]
    )

    print("13. Renombrando columna TIPO...", flush=True)

    # Renombrar Tipo
    resultados.rename(columns={"Tipo": "TIPO"}, inplace=True)

    print("14. Guardando Excel...", flush=True)

    with pd.ExcelWriter(archivo_salida, engine="xlsxwriter") as writer:
        resultados.to_excel(
            writer,
            index=False,
            sheet_name="DATA"
        )

    print(f"15. Finalizado en {time.time() - inicio:.2f} segundos", flush=True)
