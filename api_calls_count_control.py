import boto3
import datetime

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    # Tiempo de ahora y 24 horas atrás
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=1)
    
    namespace = 'AWS/ApiGateway'
    api_stage = 'test'
    api_name = 'meli-sorter-api'

    # Obtener métricas de API Gateway
    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName='Count',
        Dimensions=[
            {'Name': 'ApiName', 'Value': api_name},
            {'Name': 'Stage', 'Value': api_stage}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=2592000,  # 1 día
        Statistics=['Sum']
    )
    
    count = 0
    datapoints = response.get('Datapoints', [])
    if datapoints:
        count = int(datapoints[0]['Sum'])

    print(f"Llamadas en las últimas 24h: {count}")

    # Enviar ese dato como métrica personalizada acumulativa
    cloudwatch.put_metric_data(
        Namespace='Custom/APIUsage',
        MetricData=[
            {
                'MetricName': 'MonthlyAPICalls',
                'Timestamp': end_time,
                'Value': count,
                'Unit': 'Count',
                'StorageResolution': 60
            },
        ]
    )

    return {
        'statusCode': 200,
        'body': f'Se enviaron {count} llamadas como métrica personalizada.'
    }
