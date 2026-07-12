# División de Incapacidades

API desarrollada en Flask para procesar archivos de incapacidades de Colombia y Perú.

## Funcionalidades

- Procesamiento de incapacidades de Colombia.
- Procesamiento de incapacidades de Perú.
- Recepción de archivos Excel mediante una API REST.
- Retorno automático del archivo procesado.

## Tecnologías

- Python
- Flask
- Pandas
- OpenPyXL

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución local

```bash
python app.py
```

La API quedará disponible en:

```
http://localhost:5000
```

## Endpoint

```
POST /procesar
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| archivo | File | Archivo Excel |
| pais | String | Colombia o Peru |

## Respuesta

Archivo Excel procesado.
