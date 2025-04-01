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

## Como lo realicé

El hosting del desarrollo lo realicé en AWS, la API es una HTTP API en API Gateway que recibe los llamados del navegador para mostrar los ordenamientos posibles por un lado y recibe los llamados para reordenar el listado por otro. La API dispara una función Lambda que ejecuta los llamados a la API de Mercado Libre para obtener los datos solicitados. Dado el peso de las librerías utilizadas en el código fuente del backend, los archivos fueron empaquetados con Docker y subidos como una imagen a ECR que luego se linkeó a la función Lambda. Una vez obtenidos los datos, se ordenan en función del ordenamiento elegido en el script de contenido de javascript que se ejecuta en Chrome y se renderizan para mostrarlos con un formato similar al de Mercado Libre.
Los tokens utilizados para conectarse a la API de Mercado Libre son guardados y obtenidos de Parameter Store del servicio de System Manager de AWS. Las credenciales de AWS son obtenidas de Secrets Manager.

## Links utiles

1. <a href="https://developers.mercadolibre.com.ar/devcenter">MercadoLibre Dev Center</a> - Pagina web de developeres de Mercado Libre para construir apps en la plataforma.
2. <a href="https://developers.mercadolibre.com.ar/es_ar/api-docs-es">MercadoLibre API Docs</a> - Documentacion de endpoints de las distintas APIs de Mercado Libre, consideraciones de diseño, novedades de las APIs y guias de comienzo y autenticacion.
3. <a href="https://aws.amazon.com/es/free/?all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc&awsf.Free%20Tier%20Types=*all&awsf.Free%20Tier%20Categories=*all">AWS Pricing</a> - AWS Free Tier para calculo de costos.
   
## Instalacaiones requeridas


## Consideraciones de diseño, limitaciones y dificultades encontradas

1. Como API Gateway tiene un limite de demora de respuesta de 30 segundos y los llamados a la API de Mercado Libre para devolver todo el listado de productos ya ordenado todo en un llamado demoraba mas de 30 segundos, decidi aplicar paginacion y realizar llamados de a "chunks" de items y ordenarlos en Javascript al momento de renderizar los productos y realizar recursivamente este proceso hasta llegar al final del total de items. Actualmente se hacen llamados de a 10 items y se los inyecta y ordena en el HTML a medida que se van obteniendo de la API. Cuando se realiza el siguiente llamado de los proximos 10 items, se evaluan los 20 items actuales y se los vuelve a ordenar. Esto lo realice asi para ir mostrando resultados temporales y no esperar por una respuesta entera que demore mucho y sea abrumador para el usuario.
