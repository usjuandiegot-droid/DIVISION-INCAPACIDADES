from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from io import BytesIO
import tempfile
import zipfile
import os

from procesador import procesar_colombia, procesar_peru

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "mensaje": "API División de Incapacidades funcionando"
    })


@app.route("/procesar", methods=["POST"])
def procesar():

    print("===== NUEVA PETICIÓN =====")
    print("Archivos:", request.files)

    archivo_colombia = request.files.get("colombia")
    archivo_peru = request.files.get("peru")

    if archivo_colombia is None and archivo_peru is None:
        return jsonify({
            "error": "Debe enviar al menos un archivo."
        }), 400

    with tempfile.TemporaryDirectory() as temp_dir:

        archivos_generados = []

        ##############################################
        # COLOMBIA
        ##############################################

        if archivo_colombia:

            ruta_entrada = os.path.join(
                temp_dir,
                secure_filename(archivo_colombia.filename)
            )

            archivo_colombia.save(ruta_entrada)

            ruta_salida = os.path.join(
                temp_dir,
                "Base Globant.xlsx"
            )

            print("Procesando Colombia...", flush=True)

            procesar_colombia(
                ruta_entrada,
                ruta_salida
            )

            archivos_generados.append(ruta_salida)

        ##############################################
        # PERÚ
        ##############################################

        if archivo_peru:

            ruta_entrada = os.path.join(
                temp_dir,
                secure_filename(archivo_peru.filename)
            )

            archivo_peru.save(ruta_entrada)

            ruta_salida = os.path.join(
                temp_dir,
                "GLOBANT PERU.xlsx"
            )

            print("Procesando Perú...", flush=True)

            procesar_peru(
                ruta_entrada,
                ruta_salida
            )

            archivos_generados.append(ruta_salida)

        ##############################################
        # SI SOLO HAY UN ARCHIVO
        ##############################################

        if len(archivos_generados) == 1:

            with open(archivos_generados[0], "rb") as f:
                archivo = BytesIO(f.read())

            archivo.seek(0)

            return send_file(
                archivo,
                as_attachment=True,
                download_name=os.path.basename(archivos_generados[0])
            )

        ##############################################
        # SI HAY DOS ARCHIVOS
        ##############################################

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zipf:

            for archivo in archivos_generados:

                zipf.write(
                    archivo,
                    arcname=os.path.basename(archivo)
                )

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="Resultado Globant.zip",
            mimetype="application/zip"
        )


if __name__ == "__main__":
    app.run(debug=True)
