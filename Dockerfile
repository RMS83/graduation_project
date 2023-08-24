# pull official base image
FROM python:latest

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
#Prohibits Python from writing pyc files to disk (equivalent to python -B option)
ENV PYTHONUNBUFFERED 1
#Prohibits Python from buffering stdout and stderr (equivalent to the python -u option)

# install dependencies
RUN pip install --no-cache-dir --upgrade pip

# install psycopg2 dependencies for alpine version
#RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

# copy requirements
COPY ./requirements.txt code/requirements.txt

# install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# copy project
COPY . /code

# file execution permissions
RUN chmod +x code/entrypoint.sh

# set work directory
WORKDIR /code

# run entrypoint.sh
ENTRYPOINT ["code/entrypoint.sh"]

#If work without docker compose (django + sqlite3)
#RUN python3 manage.py makemigrations | python3 manage.py migrate