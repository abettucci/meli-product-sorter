FROM public.ecr.aws/lambda/python:3.9

# Copia el archivo de requisitos en el directorio de trabajo
COPY requirements.txt ./

# Instala las dependencias
RUN python3.9 -m pip install -r requirements.txt -t .

# Copiar toda la carpeta api dentro del contenedor
COPY . /var/task/

# Especificar el handler que AWS Lambda ejecutará
CMD ["lambda_function.lambda_handler"]