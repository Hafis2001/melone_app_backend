web: python manage.py migrate && python create_superuser.py && python manage.py collectstatic --noinput && gunicorn backend.wsgi --log-file - --bind 0.0.0.0:$PORT
