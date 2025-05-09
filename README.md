<h1 align="center">Mercado Libre Sorter - Chrome Extension</h1>

<div align="center">
  Desarrollo de app que permite ordenar los items del listado de una busqueda en la pagina de Mercado Libre por medio de una extension de Google Chrome con la cual se interactua mediante un pop-up.
</div>
<br>

## Motivacion del proyecto

<p>
  Más de una vez me pasó que en el buscador de Mercado Libre quería ordenar los resultados por los mejores vendedores en función de sus calificaciones promedio, en función de los ítems con mejor reseña en precio-calidad por ejemplo o en función de la cantidad de respuestas respondidas pero no podía porque ese "ordenar por" no se encuentra en la pagina de Mercado Libre por el momento.
Como últimamente estuve utilizando mucho la plataforma de Mercado Libre, me propuse como proyecto personal poder desarrollar ese ordenamiento para facilitarme la búsqueda en mis compras.
<p>

## DEPRECADO

Los endpoints de la API de Mercado Libre para obtener el listado de items y los atributos de los mismos fueron bloqueados para aplicaciones de individuos y solo se pueden acceder siendo un Integrador en la plataforma de  Mercado Libre, por lo que la extensión se encuentra sin funcionar.

## Cómo funciona

Primero hay que buscar un producto en la pagina de Mercado Libre como se hace normalmente y una vez obtenidos los resultados, hacer click en el popup de la extensión, esperar que se carguen los posibles ordenamientos a seleccionar, seleccionar el tipo de ordenamiento y hacer click en Reordenar Productos. Esperar a que se reordene el listado de productos.
En los posibles ordenamientos se van a mostrar por un lado un ordenamiento por evaluaciones promedio que primero muestra los ítems con mayor cantidad de reseñas y luego con mayor promedio de evaluaciones positivas. También se puede elegir ordenar por reseñas de las características del producto, por ejemplo durabilidad, calidad de los materiales, relación precio-calidad, etc. Estas opciones dependen del producto que se haya buscado.
Por el momento no se están considerando los filtros que se seleccionen, por lo que se muestran ordenados todos los ítems de la búsqueda inicial.


## Construido con 

- Backend: Python
- Frontend: Javascript, HTML y CSS.
- Testing de endpoints: Postman.
- Versionado: Github.
- CI/CD: Docker y Github Actions.
- Desarrollo de API: función Lambda con triggers basados en API Gateway y código almacenado en ECR.
- Almacenamiento y actualización de tokens de forma segura: Secret Manager, Parameter Store.
- Almacenamiento de filtros (a futuro): Dynamo DB.
- API de Mercado Libre
- Monitoreo y seguridad:
  - Alertas de CloudWatch
  - Bot Control con WAF (web app firewall)
  - AWS Budget
    
## Como lo realicé

El hosting del desarrollo lo realicé en AWS, la API es una HTTP API en API Gateway que recibe los llamados del navegador para mostrar los ordenamientos posibles por un lado y recibe los llamados para reordenar el listado por otro. La API dispara una función Lambda que ejecuta los llamados a la API de Mercado Libre para obtener los datos solicitados. Dado el peso de las librerías utilizadas en el código fuente del backend, los archivos fueron empaquetados con Docker y subidos como una imagen a ECR que luego se linkeó a la función Lambda. Una vez obtenidos los datos, se ordenan en función del ordenamiento elegido en el script de contenido de javascript que se ejecuta en Chrome y se renderizan para mostrarlos con un formato similar al de Mercado Libre.
Los tokens utilizados para conectarse a la API de Mercado Libre son guardados y obtenidos de Parameter Store del servicio de System Manager de AWS. Las credenciales de AWS son obtenidas de Secrets Manager. 

Por ultimo pero no menos importante, para evitar sobrecostos como consecuencia de un volumen de requests muy grande no previsto o algun bot que realice muchas llamadas seguidas, se realizaron las siguientes configuraciones:
  - Rate Limiting:
    - API Gateway: se configuró un Rate Limiting de 5 requests por segundo y un Burst Limit de 10 en el stage entero de la HTTP API.
  - Bot Control WAF: se configuraron reglas para controlar el origen de los requests y evitar inundar de requests la API. 
  - AWS Budget: se configuró un zero spend budget con un periodo mensual que se renueva el primer dia de cada mes y un budgeting method fijo de 1 USD y el scope considera todos los servicios de AWS. Ademas se agregan los costos por "unblended costs" que basicamente estaria sumando los costos puros de cada servicio, sin promediar descuentos o compromisos de uso entre cuentas o regiones.
  
Como AWS especifica que no deberiamos depender unicamente del throttling de la API para tener control de los costos o para bloquear el acceso a una API, esto es porque:
  - Throttling controla la velocidad, pero no el volumen mensual completo.
  - No detiene llamadas maliciosas o tráfico anómalo (bots, scrapers, DDoS).
  - No dispara acciones correctivas automáticas por sí solo
Por ende ello se creó un AWS Budget y se configuró AWS WAF para tener control del trafico de bots que pueden consumir recursos en exceso. para manejar API requests.
  
Configuracion distribucion de carga y control de acceso con Cloudfront + WAF:
- Crear una distribucion en Cloudfront.
- Crear un Web ACL (access control list) en la region Global, para poder conectarse con Cloudfront para recibir llamados de cualquier servidor.
- Crear reglas de control:
  - Maximo de requests por IP cada X tiempo.
  - Permitir solo IPs definidas (para ello hay que hacer unos llamados de ejemplo y ver que IP se utiliza desde MercadoLibre y si es fija. Esto se encuentra en los logs de CloudWatch de la funcion Lambda).
  - Filtro de user-agent sospechoso
  - Permitir requests solo con headers con la URL del listado de Mercado Libre (que "Referer" comience con "https://listado.mercadolibre.com.ar/").

Es importante resaltar que no se activó API Caching ya que dicho servicio tiene un costo asociado.

## Links utiles

1. <a href="https://developers.mercadolibre.com.ar/devcenter">MercadoLibre Dev Center</a> - Pagina web de developeres de Mercado Libre para construir apps en la plataforma.
2. <a href="https://developers.mercadolibre.com.ar/es_ar/api-docs-es">MercadoLibre API Docs</a> - Documentacion de endpoints de las distintas APIs de Mercado Libre, consideraciones de diseño, novedades de las APIs y guias de comienzo y autenticacion.
3. <a href="https://aws.amazon.com/es/free/?all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc&awsf.Free%20Tier%20Types=*all&awsf.Free%20Tier%20Categories=*all">AWS Pricing</a> - AWS Free Tier para calculo de costos.
   
## Instalacaiones requeridas

1. Crear una app en el <a href="https://developers.mercadolibre.com.ar/devcenter">Dev Center</a> de Mercado Libre y seleccionar el scope de items, o bien seguir los pasos de <a href="https://developers.mercadolibre.com.ar/es_ar/crea-una-aplicacion-en-mercado-libre-es">como crear una app</a> en la documentacion de la API de Mercado Libre.
2. Con el app ID y el redirect URI obtener el TG code para obtener el access token, el refresh token inicial y el tiempo hasta su expiracion. Almacenar estos datos como parametros iniciales en Parameter Store para comenzar a utilizar la API de Mercado Libre y luego renovar los tokens cuando se venza el access token, o bien seguir los pasos del <a href=" https://developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion">flujo de autenticacion y autorizacion</a> en la documentacion de la API de Mercado Libre.

![Flujo de auth de API Mercado Libre](https://github.com/abettucci/meli-product-sorter/blob/main/images/flujo_auth_meli.jpg)

**Extra:**

**1. Para probar los recursos de AWS de forma local se necesita primero haberse loguearse desde la terminal.**  
  **1.1 Logueo en AWS en una terminal de Windows:**
  ```bash
  aws configure
  Cuando se solicite AWS Access Key ID => es el de 22 caracteres
  Cuando se solicite AWS Secret Access Key => es el de 40 caracteres
  ```

  **1.2 Construir una imagen en Docker y pushearla al repo de ECR (iniciar Docker como primer paso):**
  ```bash
  aws ecr get-login-password --region {ECR-AWS-ZONE} | docker login --username AWS --password-stdin {AWS-ACCOUNT-ID}.dkr.ecr.{ECR-AWS-ZONE}.amazonaws.com/{ECR-REPO-NAME}
  docker build -t my-lambda-image-test -f Dockerfile .
  docker tag my-lambda-image-test:latest {AWS-ACCOUNT-ID}.dkr.ecr.{ECR-AWS-ZONE}.amazonaws.com/{ECR-REPO-NAME}:latest
  docker push {AWS-ACCOUNT-ID}.dkr.ecr.{ECR-AWS-ZONE}.amazonaws.com/{ECR-REPO-NAME}:latest
  ```

**1.3 Consultar costos con AWS Cost Explorer para validar no haber iniciado algun recurso que no sea gratuito.**
  **1.3.1 Politicas IAM necesaria a nivel usuario:**    
  ```yaml
    {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": [
                  "ce:GetCostAndUsage",
                  "ce:GetCostForecast",
                  "ce:GetUsageForecast",
                  "ce:GetReservationUtilization",
                  "ce:DescribeCostCategoryDefinition",
                  "ce:ListCostAllocationTags"
              ],
              "Resource": "*"
          }
      ]
    }
  ```
  **1.3.2 Codigo a correr en la terminal para conocer los costos actuales de cada servicio en uso en un periodo de tiempo por su tiempo/volumen de uso:**
  ```bash
  aws ce get-cost-and-usage --time-period Start=2024-09-01,End=2024-09-30 --granularity MONTHLY --metrics "BlendedCost" --group-by Type=DIMENSION,Key=SERVICE Type=TAG,Key=USAGE_TYPE
  ```
    
  **1.3.3 Codigo a correr en la terminal para conocer el pronostico de costos de cada servicio en un periodo de tiempo estimado:**    
  ```bash
  aws ce get-cost-forecast --time-period Start=2024-10-01,End=2024-12-31 --metric BLENDED_COST --granularity MONTHLY
  ```

 ## Políticas IAM requeridas por el rol de la funcion Lambda en AWS

**1. Obtener y colocar parametros en Parameter Store del servicio de System Manager:**  
  ```yaml
  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": [
                  "ssm:GetParameter",
                  "ssm:PutParameter"
              ],
              "Resource": "arn:aws:ssm:<your-app-aws-zone>:<your-aws-account-id>:parameter/mercado_libre/token"
          },
          {
              "Effect": "Allow",
              "Action": [
                  "kms:Decrypt"
              ],
              "Resource": "*"
          }
      ]
  }
  ```

**2. Obtener y colocar datos en las tablas de Dynamo DB:**
  ```yaml
  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": [
                  "dynamodb:PutItem",
                  "dynamodb:GetItem",
                  "dynamodb:Query",
                  "dynamodb:Scan"
              ],
              "Resource": "arn:aws:dynamodb:<your-app-aws-zone>:<your-aws-account-id>::table/UserFilters"
          }
      ]
  }
  ```

**3. Obtener metricas de consumo de servicios para controlar costos:**
```yaml
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:PutMetricData"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
```

## Políticas IAM requeridas por el usuario en AWS

**1. Secrets Manager Read and Write secret keys: adjuntar la politica para poder acceder a los secretos guardados en el servicio de Secrets Manager y poder utlizar el ACCESS_KEY y SECRET_ACCESS_KEY de AWS.**
  ```yaml 
  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": [
                  "secretsmanager:GetSecretValue",
                  "kms:Decrypt"
              ],
              "Resource": [
                  "arn:aws:secretsmanager:<your-aws-region>:<your-aws-account-id>:secret:<your-first-secret-name>",
                  "arn:aws:secretsmanager:<your-aws-region>:<your-aws-account-id>:secret:<your-second-secret-name>"
              ]
          }
      ]
  }
  ```
**2. ECR Put and Get images: crear y adjuntar la politica para que se pueda conectar una funcion Lambda a una imagen de un repo de ECR.**
  ```yaml
  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": [
                  "ecr:GetDownloadUrlForLayer",
                  "ecr:GetAuthorizationToken",
                  "ecr:BatchCheckLayerAvailability",
                  "ecr:BatchGetImage",
                  "ecr:GetRepositoryPolicy",
                  "ecr:ListImages",
                  "ecr:PutImage",
                  "ecr:DescribeImages",
                  "ecr:DescribeRepositories",
                  "ecr:GetLifecyclePolicyPreview",
                  "ecr:GetLifecyclePolicy"
              ],
              "Resource": "arn:aws:ecr:<your-aws-region>:<your-aws-account-id>:repository/<your-ecr-repo-name>"
          }
      ]
  }
  ```

**3. Habilitar logs de WAF para controlar las IP que llegan a Cloudfront**
```yaml
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowCreateLogStreamAndPutLogEvents",
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:log-group:/aws/waf/*:log-stream:*"
      },
      {
        "Sid": "AllowDescribeLogGroupsAndStreams",
        "Effect": "Allow",
        "Action": [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ],
        "Resource": "*"
      }
    ]
  }
```

## Consideraciones de diseño, limitaciones y dificultades encontradas

1. Como API Gateway tiene un limite de demora de respuesta de 30 segundos y los llamados a la API de Mercado Libre para devolver todo el listado de productos ya ordenado todo en un llamado demoraba mas de 30 segundos, decidi aplicar paginacion y realizar llamados de a "chunks" de items y ordenarlos en Javascript al momento de renderizar los productos y realizar recursivamente este proceso hasta llegar al final del total de items. Actualmente se hacen llamados de a 10 items y se los inyecta y ordena en el HTML a medida que se van obteniendo de la API. Cuando se realiza el siguiente llamado de los proximos 10 items, se evaluan los 20 items actuales y se los vuelve a ordenar. Esto lo realice asi para ir mostrando resultados temporales y no esperar por una respuesta entera que demore mucho y sea abrumador para el usuario.
2. API Gateway de AWS cuenta con un free tier de 1 millon de llamados gratis por mes.
3. Elastic Container Registry cuenta con un free tier hasta 500 MB por mes en el total de imagenes almacenadas (esto es clave a la hora de seleccionar las librerias que no sean tan pesadas, actualmente la imagen del backend tiene un peso de 285 MB).  El costo por el excedente es de 0,1 USD/GB adicional. Por cada actualizacion del codigo en Github se ejecuta Github Actions que es un CI/CD externo a AWS y hace un rebuild de la imagen y un push a ECR, por esta transferencia de datos de Github a AWS se cobra 0,01 USD por cada GB de datos transferidos, es decir, si la imagen pesa 250 MB aprox, se necesitan 40 actualizaciones de codigo para que se cobre 0,01 USD. Por ultimo, Lambda siempre utiliza una imagen cacheada de ECR por lo que no tiene costo esa conexion, salvo que se haga un push de una iamgen nueva. En ese caso, Lambda debe hacer un nuevo pull de la iamgen y por cada 1000 requests de pull se cobra 0,001 USD.
4. Lambda Function cuenta con un free tier de 1 millon de llamados gratis por mes. Luego se cobra 0,20 USD por cada millón de solicitudes excedentes y 0,0000166667 USD por cada GB/segundo de procesamiento hasta llegar a los primeros 6 mil millones de GB/segundo por mes.
5. Parameter Store cuenta con un free tier por el servicio estandar, sin embargo, se cobra 0,05 USD por cada 10.000 interacciones de la API, o sea por cada 10.000 autenticaciones que se realizan.
6. WAF & Shield cuenta con un free tier de manejar hasta 10 millones de solicitudes (requests) de control de bots por mes.
7. Como AWS Shield & WAF solo permite linkear REST API a las Web ACL y no HTTP API como la que tenia creada, se decidió no migrar de HTTP a REST y en cambio se utilizó Cloudfront asociado a la Web ACL.

## Aclaraciones de costos en AWS
- 12 meses gratis: estas ofertas de la capa gratuita están disponibles exclusivamente para los nuevos clientes de AWS y solo durante doce meses a partir de la fecha de inscripción en AWS. Cuando finalicen los 12 meses de uso gratuito o si el uso de su aplicación supera las capas, tendrá que pagar las tarifas de servicio estándar por uso (consulte la página de cada servicio para obtener información completa sobre los precios). Existen restricciones; consulte las condiciones de la oferta para obtener más detalles.

- Gratis para siempre: estas ofertas de la capa gratuita no vencen automáticamente al finalizar los 12 meses de la capa gratuita de AWS, sino que están disponibles tanto para clientes ya existentes como para nuevos clientes de AWS de forma indefinida.
