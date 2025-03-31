import json
from mercado_libre import get_search_filters_dictionary, obtener_productos_de_api, obtener_caracteristicas_calificadas_primera_publicacion
import boto3
import time
import uuid

def mostrar_categorias_de_reseñas(item_name, token_de_acceso):
    review_quanti_attributes, total_publicaciones = obtener_caracteristicas_calificadas_primera_publicacion(item_name, token_de_acceso)
    nombres_categorias_de_resenas = [attr["display_text"] for attr in review_quanti_attributes]

    print('nombres_categorias_de_resenas: ', nombres_categorias_de_resenas)

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS, POST, GET",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps({
            "nombres_categorias_de_resenas": nombres_categorias_de_resenas,
            "total_publicaciones" : total_publicaciones
        })
    }

def store_filter(data):
    # Inicializar cliente de DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("UserFilters")

    try:
        session_id = data.get("session_id", str(uuid.uuid4()))  # Generar ID si no se envía
        producto = data.get("producto")
        filtros_disponibles = data.get("filtros_disponibles", {})
        de_para_filtros = data.get("de_para_filtros", {})
        de_para_filtros_values = data.get("de_para_filtros_values", {})

        if not filtros_disponibles:
            return {"statusCode": 400, "body": json.dumps({"error": "No filters provided"})}

        timestamp = int(time.time())  # Obtener timestamp UNIX

        # Guardar en DynamoDB
        table.put_item(
            Item={
                "session_id": session_id,
                "timestamp": timestamp,
                "producto" : producto,
                "filtros_disponibles": filtros_disponibles,
                "de_para_filtros" : de_para_filtros,
                "de_para_filtros_values" : de_para_filtros_values
            }
        )     

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, POST, GET",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({"message": "Filters saved successfully", "session_id": session_id})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def format_filters(data):
    filtros_recibidos = data.get("filtros", {}) 
    filtros_recibidos.pop("q", None)
    de_para_filtros = data.get("de_para_filtros", {}) 
    de_para_filtros_values = data.get("de_para_filtros_values", {})

    print('filtros_recibidos: ', filtros_recibidos)
    print(de_para_filtros)
    print(de_para_filtros_values)

    filtros_convertidos = ''
    for key, value in filtros_recibidos.items():
        value_id = de_para_filtros.get(value, "")

        filtro_formateado = de_para_filtros_values.get(value_id, "") + '=' + value_id

        if filtros_convertidos:
            filtros_convertidos += '&' + filtro_formateado
        else:
            filtros_convertidos = filtro_formateado

    print(filtros_convertidos)
    
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS, POST, GET",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(filtros_convertidos)
    }

def get_stored_filters(producto):
    # Inicializar cliente de DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("UserFilters")

    try:
        response = table.scan()  # Obtener todos los items de la tabla
        items = response.get("Items", [])

        for item in items:
            if item.get("producto") == producto:
                filtros_disponibles = item.get("filtros_disponibles")
                de_para_filtros = item.get("de_para_filtros")
                de_para_filtros_values = item.get("de_para_filtros_values")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, POST, GET",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({
                "filtros_disponibles": filtros_disponibles,
                "de_para_filtros" : de_para_filtros,
                "de_para_filtros_values" : de_para_filtros_values
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error al obtener filtros almacenados"})
        }

def obtener_filtros(params, token_de_acceso):
    producto = params.get('producto', '')
    filters_values_dict, filters_values_id_dict, de_para_filtros_dict, de_para_filtros_values_dict = get_search_filters_dictionary(producto, token_de_acceso)
    
    print('filters_values_dict: ', filters_values_dict)
    
    filtros_disponibles = {
        'Ubicacion': filters_values_dict.get("Ubicación", []),
        'Ubicación de retiro': filters_values_dict.get("Ubicación de retiro", []),
        'Condicion': filters_values_dict.get("Condición", []),
        'Marca': filters_values_dict.get("Marca", []),
        'Precio': filters_values_dict.get("Precio", []),
        'Financiación': filters_values_dict.get("Financiación", []), 
        'Tiendas oficiales': filters_values_dict.get("Tiendas oficiales", []), 
        'Costo de envío': filters_values_dict.get("Costo de envío", []),
        'Otras características': filters_values_dict.get('Otras características', []),
    }

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS, POST, GET",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps({
            "filtros_disponibles": filtros_disponibles,
            "de_para_filtros": de_para_filtros_dict,
            "de_para_filtros_values": de_para_filtros_values_dict
        })
    }

def obtener_lista_productos(producto, token_de_acceso, limit=10, offset=0):
    if not producto:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "El parámetro 'q' es obligatorio"})
        }

    try:
        productos = obtener_productos_de_api(producto, token_de_acceso, limit, offset)
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, POST, GET",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps(productos)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Error interno en la API: {str(e)}"})
        }