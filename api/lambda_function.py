import json
from handlers import store_filter, format_filters, obtener_filtros, obtener_lista_productos, get_stored_filters, mostrar_categorias_de_reseñas
from auth import logueos

def lambda_handler(event, context):
    token_de_acceso = logueos()

    path = event["rawPath"]
    http_method = event["requestContext"]["http"]["method"]
    body = json.loads(event["body"]) if event.get("body") else {}

    if path == "/{STAGE}/get-reviews-filters" and http_method in ["GET"]:
        return mostrar_categorias_de_reseñas(event.get("queryStringParameters", {}), token_de_acceso)
    
    elif path == "/{STAGE}/filtros" and http_method == "GET":
        return obtener_filtros(event.get("queryStringParameters", {}), token_de_acceso)
    
    elif path == "/{STAGE}/store-filters" and http_method == "POST":
        return store_filter(body)

    elif path == "/{STAGE}/get-stored-filters" and http_method == "GET":
        producto = event.get("queryStringParameters", {}).get('producto', '')
        return get_stored_filters(producto)
    
    elif path == "/{STAGE}/format-filters" and http_method in ["POST"]:
        return format_filters(body)
    
    elif path == "/{STAGE}/productos" and http_method == "POST":
        producto = body.get("q")
        limit = int(body.get("limit", 10))
        offset = int(body.get("offset", 0))
        return obtener_lista_productos(producto, token_de_acceso, limit, offset)

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Endpoint no encontrado"})
    }