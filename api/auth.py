import requests
import json
import boto3, boto3.session
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import pytz

# Cliente AWS SSM para Parameter Store
ssm_client = boto3.client("ssm", region_name="YOUR_AWS_ZONE")
PARAMETER_NAME = "/path-to-token"

def get_secret_value_aws(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="YOUR_AWS_ZONE")
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return secret

# Funcion para regenerar el token de acceso a la API de MELI 
def get_access_token(app_id, secret_client_id, refresh_token):
    url = "https://api.mercadolibre.com/oauth/token"
    payload = f"grant_type=refresh_token&client_id={app_id}&client_secret={secret_client_id}&refresh_token={refresh_token}"
    headers = {'accept': 'application/json','content-type': 'application/x-www-form-urlencoded'}
    response = requests.request("POST", url, headers=headers, data=payload)
    data = json.loads(response.text)
    proximo_refresh_token = data.get('refresh_token', None)
    access_token = data.get('access_token', None)
    t_expiracion = data.get('expires_in', None)
    return proximo_refresh_token, access_token, t_expiracion

def logueos():
    # Obtener la hora actual en zona horaria de Buenos Aires
    buenos_aires_timezone = pytz.timezone('America/Argentina/Buenos_Aires')
    current_time = datetime.now(buenos_aires_timezone)

    # Obtener el parámetro desde AWS Parameter Store
    try:
        response = ssm_client.get_parameter(Name=PARAMETER_NAME, WithDecryption=True)
        tokens_data = json.loads(response["Parameter"]["Value"])
    except ssm_client.exceptions.ParameterNotFound:
        raise Exception(f"El parámetro {PARAMETER_NAME} no existe en AWS Parameter Store.")

    refresh_token = tokens_data["refresh_token"]
    access_token = tokens_data["access_token"]
    t_expiracion = datetime.strptime(tokens_data["expiracion"], '%Y-%m-%d %H:%M:%S')
    t_expiracion = buenos_aires_timezone.localize(t_expiracion)
    app_id = tokens_data["app_id"]
    secret_client_id = tokens_data["secret_client_id"]

    # Si el token sigue siendo válido, lo usamos
    if current_time < t_expiracion:
        return access_token

    # Si el token ha expirado, obtenemos uno nuevo
    proximo_refresh_token, nuevo_access_token, tiempo_de_expiracion = get_access_token(app_id, secret_client_id, refresh_token)

    # Calcular nueva fecha de expiración
    nueva_expiracion = current_time + timedelta(seconds=tiempo_de_expiracion)
    nueva_expiracion_str = nueva_expiracion.strftime('%Y-%m-%d %H:%M:%S')

    # Guardar los nuevos valores en AWS Parameter Store
    nuevo_valor = {
        "refresh_token": proximo_refresh_token,
        "access_token": nuevo_access_token,
        "expiracion": nueva_expiracion_str,
        "app_id": app_id,
        "secret_client_id": secret_client_id
    }

    ssm_client.put_parameter(
        Name=PARAMETER_NAME,
        Value=json.dumps(nuevo_valor),
        Type="SecureString",
        Overwrite=True
    )

    return nuevo_access_token