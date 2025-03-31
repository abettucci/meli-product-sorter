import requests
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def get_request(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response

def get_answered_questions(item_id, token_de_acceso):
    url = f"https://api.mercadolibre.com/questions/search?item={item_id}&api_version=4"
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    faq_dict = dict()
    cant_respuestas = 0
    cant_preguntas = response.json()["total"]
    preguntas = response.json()["questions"]
    for pregunta in preguntas:
        question = pregunta["text"]
        if pregunta["answer"]:
            if pregunta["answer"]["text"].lower():
                faq_dict[question] = pregunta["answer"]["text"].lower()
                cant_respuestas += 1

    return faq_dict, cant_preguntas, cant_respuestas
    
def get_seller_info(seller_id, token_de_acceso):
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()

def get_items(next_page_url, token_de_acceso):
    # Traer en orden de relevancia o de winner de catalogo (hay un parametro que es "order_backend" en catalogo creo)
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", next_page_url, headers=headers, data=payload)
    data = response.json()
    return data

# Busqueda por nombre de producto. Docu: https://developers.mercadolibre.com.ar/es_ar/items-y-busquedas#Obtener-%C3%ADtems-de-una-consulta-de-b%C3%BAsqueda
def get_items_from_name_search(item_name, filtros, token_de_acceso, limit, offset):
    # El limit es maximo de a 100 publicaciones por pagina. Con el search_type = scan podemos traer hasta 1000 registros (creo que no funca para busqueda por query search)
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={item_name}&offset={offset}&limit={limit}"
    if filtros:
        url += "&" + filtros
    
    print('url: ', url)

    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    
    print('total: ', data.get('paging', {}).get('total', 0))
    print('Items devueltos: ', len(data.get('results', [])))

    return data.get('results', []), data.get('paging', {}).get('total', 0)

def get_search_filters_dictionary(item_name, token_de_acceso):
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={item_name}&offset=0&include_filters=true"
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = get_request(url, headers=headers).json()
    available_filters = response["available_filters"]

    filters_values_dict = dict()
    filters_values_id_dict = dict()
    de_para_filtros_dict = dict()
    de_para_filtros_values_dict = dict()
    
    for filter in available_filters:
        values = filter['values']
        for value in values:
            filters_values_id_dict[filter['id']] = value['id']

    for filter in available_filters:
        values = filter['values']
        for value in values:
            
            if list(filters_values_dict.keys()) == []:
                filters_values_dict[filter['name']] = [value['name']]
            elif filter['name'] in list(filters_values_dict.keys()):
                filters_values_dict[filter['name']].append(value['name'])
            else: 
                filters_values_dict[filter['name']] = [value['name']]

    for filter in available_filters:
        values = filter['values']
        for value in values:
            de_para_filtros_dict[value['name']] = value['id']

            de_para_filtros_values_dict[value['id']] = filter['id']

    return filters_values_dict, filters_values_id_dict, de_para_filtros_dict, de_para_filtros_values_dict

def get_visitas_publicacion(item_id_con_mla, fecha_inicio, fecha_fin, token_de_acceso): #fecha en formato 2024-08-01
    url = f"https://api.mercadolibre.com/items/visits?ids={item_id_con_mla}&date_from={fecha_inicio}&date_to={fecha_fin}"
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    
    return response.json()

def get_reviews(item_id_con_mla, token_de_acceso):
    url = f"https://api.mercadolibre.com/reviews/item/{item_id_con_mla}"
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()

    review_attributes, total_reviews, rating_average, one_star, two_star, three_star, four_star, five_star = \
        data.get('quanti_attributes', [])\
            , data.get('paging', {}).get("total", None)\
                , data.get('rating_average', None)\
                    , data.get("rating_levels", {}).get("one_star", None)\
                        , data.get("rating_levels", {}).get("two_star", None)\
                            , data.get("rating_levels", {}).get("three_star", None)\
                                , data.get("rating_levels", {}).get("four_star", None)\
                                    , data.get("rating_levels", {}).get("five_star", None)

    return review_attributes, total_reviews, rating_average, one_star, two_star, three_star, four_star, five_star

# Me traigo las caracteristicas del primer producto usandolo como proxy de toda la categoria para mostrarlos en los filtros/ordenamientos
def obtener_caracteristicas_calificadas_primera_publicacion(item_name, token_de_acceso): 
    primer_item, total_publicaciones =  get_items_from_name_search(item_name, '', token_de_acceso, 1, 0)

    print('primer_item: ', primer_item)

    primer_item = primer_item[0]
    item_id_con_mla = primer_item['id']
    review_attributes, total_reviews, rating_average, one_star, two_star, three_star, four_star, five_star = get_reviews(item_id_con_mla, token_de_acceso)
    review_quanti_attributes = [{ "name": attr["name"], "display_text": attr["display_text"] } for attr in review_attributes]

    print('review_quanti_attributes: ', review_quanti_attributes)

    return review_quanti_attributes, total_publicaciones

def obtener_ciudades_de_provincia(estado, token_de_acceso):
    url = f"https://api.mercadolibre.com/classified_locations/states/{estado}"
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_acceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    cities = response.json()["cities"]

    return cities

def cuando_llega(item_id, city_id, token_de_accceso):
    url = f"https://api.mercadolibre.com/items/{item_id}/shipping_options?city_to={city_id}"
    payload = {}
    headers = {'Authorization': 'Bearer ' + token_de_accceso}
    response = requests.request("GET", url, headers=headers, data=payload)
    # chequear que hay varios tipos de envios y vaira el cuando llega: prioritario, standard, etc.
    cuando_llega = response.json()["options"][0]["shipping_method_type"] # next_day
    return cuando_llega

def obtener_productos_de_api(item_name, token_de_acceso, limit, offset):
    items_scrapeados, total_publicaciones =  get_items_from_name_search(item_name, '', token_de_acceso, limit, offset)
    
    dict_provincias = {
        'AR-B' : 'Buenos Aires',
        'AR-C' : 'Capital Federal',
        'AR-Y' : 'Jujuy',
        'AR-M' : 'Mendoza',
        'AR-E' : 'Entre Ríos',
        'AR-T' : 'Tucumán',
        'AR-W' : 'Corrientes',
        'AR-U' : 'Chubut',
        'AR-D' : 'San Luis',
        'AR-A' : 'Salta',
        'AR-F' : 'La Rioja',
        'AR-G' : 'Santiago del Estero',
        'AR-H' : 'Chaco',
        'AR-J' : 'San Juan',
        'AR-K' : 'Catamarca',
        'AR-L' : 'La Pampa',
        'AR-N' : 'Misiones',
        'AR-P' : 'Formosa',
        'AR-Q' : 'Neuquen',
        'AR-R' : 'Río Negro',
        'AR-S' : 'Santa Fe',
        'AR-V' : 'Tierra del Fuego',
        'AR-X' : 'Córdoba',
        'AR-Z' : 'Santa Cruz'
    }

    # ciudades = []
    # for prov in list(dict_provincias.keys()):
    #     ciudades.append(obtener_ciudades_de_provincia(prov, token_de_acceso))
    
    dict_vendors_name_and_city = dict()
    dict_items = dict()
    data_diccionario_items = []
    data_diccionario_sellers = []

    for item in items_scrapeados:
        item_id_con_mla = item['id']
        item_url = item['permalink'].replace('http://', 'https://')
        seller_id = item['seller']['id']

        portada = item['thumbnail'].replace('http://', 'https://')
        titulo = item['title']
        sale_price = item['sale_price']['amount']

        if item.get('installments') == None:
            quantity_cuotas = ''
            tasa_financiacion = ''
            sale_price_per_cuota = ''
        else:
            quantity_cuotas = item.get('installments', {}).get('quantity', '')
            tasa_financiacion = item.get('installments', {}).get('quantity', '')
            sale_price_per_cuota = item.get('installments', {}).get('amount', '')

        shipping = item['shipping']['tags']
        free_shipping = item['shipping']['free_shipping']
        tipo_envio = item['shipping']['logistic_type'] 

        try:
            faq_dict, cant_preguntas, cant_respuestas = get_answered_questions(item_id_con_mla, token_de_acceso)

            fecha_hoy = datetime.now()
            fecha_hace_3_meses = fecha_hoy - relativedelta(months=3)

            fecha_inicio, fecha_fin = (fecha_hace_3_meses.strftime('%Y-%m-%d'), fecha_hoy.strftime('%Y-%m-%d'))
            cantidad_visitas_l3m = get_visitas_publicacion(item_id_con_mla, fecha_inicio, fecha_fin, token_de_acceso)[0]["total_visits"]
            
            seller_info = get_seller_info(seller_id, token_de_acceso)
            seller_city, seller_state, seller_nickname, seller_level, seller_txs, power_seller_status = seller_info["address"]["city"], seller_info["address"]["state"], seller_info["nickname"], seller_info["seller_reputation"]["level_id"], seller_info["seller_reputation"]["transactions"]["total"], seller_info["seller_reputation"]["power_seller_status"]
        
            review_attributes, total_reviews, rating_average, one_star, two_star, three_star, four_star, five_star = get_reviews(item_id_con_mla, token_de_acceso)

            if item_id_con_mla not in list(dict_items.keys()):
                dict_items[item_id_con_mla] = [item_url, cant_preguntas, cant_respuestas, cantidad_visitas_l3m, rating_average, one_star, 
                                                two_star, three_star, four_star, five_star, seller_id, review_attributes, total_reviews, 
                                                    portada, titulo, sale_price, shipping, tipo_envio, sale_price_per_cuota, quantity_cuotas, tasa_financiacion, free_shipping]            

            # Rellenamos el diccionario de vendedores y ubicacion
            if seller_nickname not in list(dict_vendors_name_and_city.keys()):
                dict_vendors_name_and_city[seller_nickname] = [seller_level, seller_txs, seller_city, seller_state, seller_id, power_seller_status]
            
        except:
            pass

    # Rellenamos el diccionario de items
    for item_id_con_mla, item_values in dict_items.items():
        fila = {
            "seller_id" : item_values[10],
            "item_id" : item_id_con_mla,
            "item_url" : item_values[0],
            "visitas_l3m" : item_values[3],
            "cant_preguntas" : item_values[1],
            # "pct_respuesta" : str(round((item_values[2]/item_values[1]) if item_values[1] != 0 else 0,2)),
            "cant_respuestas" : item_values[2],
            "review_attributes" : item_values[11], 
            "total_reviews" : item_values[12],
            "rating_average" : item_values[4],
            "one_star": item_values[5], 
            "two_star" : item_values[6], 
            "three_star" : item_values[7], 
            "four_star" : item_values[8], 
            "five_star" : item_values[9],
            "portada" : item_values[13],
            "titulo" : item_values[14],
            "sale_price" : item_values[15],
            "shipping" : item_values[16],
            "tipo_envio" : item_values[17],
            "sale_price_per_cuota" : item_values[18], 
            "quantity_cuotas" : item_values[19],
            "tasa_financiacion" : item_values[20],
            "free_shipping" : item_values[21]
        }
        data_diccionario_items.append(fila)
    
    df_reputacion_items = pd.DataFrame(data_diccionario_items)
    
    # Rellenamos el diccionario de sellers
    for seller_nickname, seller_values in dict_vendors_name_and_city.items():
        fila = {
            "seller_id" : seller_values[4],
            "seller_nickname" : seller_nickname,
            "seller_city" : seller_values[2],
            "seller_state" : seller_values[3],
            "seller_level" : seller_values[0], 
            "seller_txs" : seller_values[1],
            "power_seller_status" : seller_values[5]
        }
        data_diccionario_sellers.append(fila)

    df_reputacion_vendors = pd.DataFrame(data_diccionario_sellers)
    df_reputacion_vendors_sin_dup = df_reputacion_vendors.drop_duplicates(subset=["seller_nickname"], keep='first')

    df_reputacion_vendors_sin_dup['seller_state'] = df_reputacion_vendors_sin_dup['seller_state'].map(dict_provincias)

    df_merged = pd.merge(df_reputacion_items, df_reputacion_vendors_sin_dup, how='left', on='seller_id')
    df_merged = df_merged.drop('seller_id', axis=1)

    df_merged['review_attributes'] = df_merged['review_attributes'].apply(lambda x: x if isinstance(x, list) else [])

    return df_merged.to_dict('records')