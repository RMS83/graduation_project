#!/bin/sh
#sleep 10

python manage.py makemigrations
python manage.py makemigrations order_app
python manage.py migrate

#For Redis
#python manage.py createcachetable

# Option 1. executing a file to create a superuser
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$POSTGRES_DB" ]
  then
    echo "creating a superuser - ${DJANGO_SUPERUSER_USERNAME}."
    python manage.py createsuperuser \
        --noinput \
        --email $DJANGO_SUPERUSER_EMAIL \
        --first_name $DJANGO_SUPERUSER_NAME \
        --last_name $DJANGO_SUPERUSER_SURNAME \

    echo "CREATED SUPERUSER"
fi

#
# Option 2. executing a file to create a superuser
#if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$POSTGRES_DB" ]
#  then
#    echo "creating a superuser - ${DJANGO_SUPERUSER_EMAIL}."
#    echo "from django.contrib.auth import get_user_model" > administry.py
#    echo "User = get_user_model()" >> administry.py
#    echo "User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_NAME', '$DJANGO_SUPERUSER_SURNAME', '$DJANGO_SUPERUSER_PASSWORD')" >> administry.py
#    python3 manage.py shell < administry.py
#    echo "CREATED SUPERUSER"
#    rm administry.py
#fi


exec "$@"
