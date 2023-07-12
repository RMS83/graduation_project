#!/bin/sh

python manage.py makemigrations
python manage.py migrate

#For Redis
#python manage.py createcachetable

if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$POSTGRES_DB" ]
  then
    echo "creating a superuser - ${DJANGO_SUPERUSER_USERNAME}."
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
    echo "CREATED SUPERUSER"
fi


## Option 2. executing a file to create a superuser
#if [ "$DJANGO_SUPERUSER_USERNAME" ]
#  then
#    echo "creating a superuser - ${DJANGO_SUPERUSER_USERNAME}."
#    echo "from django.contrib.auth import get_user_model" > administry.py
#    echo "User = get_user_model()" >> administry.py
#    echo "User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')" >> administry.py
#    python3 manage.py shell < administry.py
#    echo "CREATED SUPERUSER"
#    rm administry.py
#fi


exec "$@"
