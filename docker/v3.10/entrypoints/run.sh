# /bin/bash

# alembic
poetry run alembic -c labonneboite/alembic.ini upgrade head 

# run custom sql scripts if any
if [ ! -z "$(ls -A /sql)" ]; then
    echo 'Running sql scripts if any'
    for i in `/bin/ls -1 /sql/*.sql`; do 
        echo $i
        mysql --user=$DB_USER \
        --password=$DB_PASSWORD \
        --host=$DB_HOST \
        --port=$DB_PORT \
        --database=$DB_NAME < $i
    done
fi;

# run the server
poetry run gunicorn --config python:labonneboite.wsgi-conf labonneboite.web.app:app