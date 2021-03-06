#!/usr/bin/env bash
# Getting static files for Admin panel hosting!
set -e
echo ""
echo "================================================"
echo "= Bitoubi Api Dev docker-compose               ="
echo "================================================"
echo ""

while ! pg_isready -h $POSTGRESQL_ADDON_HOST -p $POSTGRESQL_ADDON_PORT; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done


# ./manage.py collectstatic --noinput
# ./manage.py compress --force

./manage.py migrate

./manage.py runserver 0.0.0.0:8880
# gunicorn config.wsgi:application -w 2 -b :8880 --reload
