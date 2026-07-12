from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile

from procesador import procesar_colombia, procesar_peru

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "mensaje": "API División de Incapacidades funcionando"
    })


@app.route("/procesar", methods=["POST"])
def procesar():
    print("===== NUEVA PETICIÓN =====")
    print("request.files:", request.files)
    print("request.form:", request.form)
    print("request.content_type:", request.content_type)
    
    # Validar que venga un archivo
    if "archivo" not in request.files:
        return jsonify({"error": "No se recibió ningún archivo."}), 400

    archivo = request.files["archivo"]

    if archivo.filename == "":
        return jsonify({"error": "Debe seleccionar un archivo."}), 400

    # Validar país
    pais = request.form.get("pais")

    if pais not in ["Colombia", "Peru"]:
        return jsonify({
            "error": "El parámetro 'pais' debe ser 'Colombia' o 'Peru'."
        }), 400

    # Crear carpeta temporal
    with tempfile.TemporaryDirectory() as temp_dir:

        nombre_archivo = secure_filename(archivo.filename)

        ruta_entrada = os.path.join(temp_dir, nombre_archivo)
        archivo.save(ruta_entrada)

        if pais == "Colombia":
            ruta_salida = os.path.join(temp_dir, "Base Globant.xlsx")
            procesar_colombia(ruta_entrada, ruta_salida)

        else:
            ruta_salida = os.path.join(temp_dir, "GLOBANT PERU.xlsx")
            procesar_peru(ruta_entrada, ruta_salida)

        return send_file(
            ruta_salida,
            as_attachment=True,
            download_name=os.path.basename(ruta_salida),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


if __name__ == "__main__":
    app.run(debug=True)
