#!/bin/sh

python manage.py makemigrations
python manage.py makemigrations order_app
python manage.py migrate

# Option 1. executing a file to create a superuser
if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$POSTGRES_DB" ]; then
  echo "creating a superuser - ${DJANGO_SUPERUSER_EMAIL}."
  python manage.py createsuperuser \
    --noinput \
    --email $DJANGO_SUPERUSER_EMAIL \
    --first_name $DJANGO_SUPERUSER_NAME \
    --last_name $DJANGO_SUPERUSER_SURNAME

  echo "CREATED SUPERUSER"
fi

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

if [ "$POSTGRES_DB" ]; then
  echo "-* Filling in the status model *-"
  echo "from order_app.models import Status" >order_status.py
  echo 'Status.objects.all().delete()' >>order_status.py
  echo 'Status.objects.create(name="Отменен")' >>order_status.py
  echo 'Status.objects.create(name="Подтвержден")' >>order_status.py
  echo 'Status.objects.create(name="Частично подтвержден")' >>order_status.py
  echo 'Status.objects.create(name="Доставлен")' >>order_status.py
  echo 'Status.objects.create(name="Частично доставлен")' >>order_status.py
  python3 manage.py shell <order_status.py
  echo "-* complete *-"
  rm order_status.py
  echo "-* rm complete *-"
fi

exec "$@"
