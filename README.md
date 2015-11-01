# Deployment

## Prepare

Put service files in place from deploy/ directory and set desired variables

## Postgres

ssh# mkdir -p /opt/postgres/data 
fab -u root -H <ip> deploy_postgres
ssh# systemctl stop systemd-nspawn@postgres.service
ssh# /usr/bin/systemd-nspawn -D /opt/postgres/current --setenv=PGDATA=/data --bind=/opt/postgres/data:/data bash
> chown postgres:postgres -R /data
> su postgres -c "/usr/lib/postgresql/9.3/bin/pg_ctl initdb";
> su postgres -c "/usr/lib/postgresql/9.3/bin/postgres -F --port=5433 -h 127.0.0.1 -k /tmp" &
> su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';\""
> su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';\""
> su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"DROP DATABASE template1;\""
> su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING = 'UNICODE';\""
> su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template1';\""
> su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"CREATE USER $PG_USER WITH PASSWORD '$PG_PASSWORD';\""
> su postgres -c "/usr/lib/postgresql/9.3/bin/createdb -h 127.0.0.1 -p 5433 eventsdb -O $PG_USER";
> su postgres -c "/usr/lib/postgresql/9.3/bin/createdb -h 127.0.0.1 -p 5433 admindb -O $PG_USER";

ssh# ln -s /opt/postgres/current /var/lib/machines/postgres
ssh# systemctl start systemd-nspawn@postgres.service

## Events

fab -u root -H <ip> deploy_events
ssh# systemctl stop systemd-nspawn@events_service.service
ssh# /usr/bin/systemd-nspawn -D /opt/events_service/current --setenv=DATABASE_URL=<URL> bash
> cd /work
> alembic upgrade head
> python3 manage.py add_provider ITKPI
<key returned
> python3 manage.py import <key>

ssh# ln -s /opt/events_service/current /var/lib/machines/events_service
ssh# systemctl start systemd-nspawn@events_service.service

## Redis

ssh# mkdir -p /opt/redis/data
fab -u root -H <ip> deploy_redis
ssh# ln -s /opt/redis/current /var/lib/machines/redis
ssh# systemctl restart systemd-nspawn@events_service.service


## Admin

fab -u root -H <ip> deploy_admin
ssh# ln -s /opt/admin_service/current /var/lib/machines/admin_service
ssh# /usr/bin/systemd-nspawn -D /opt/admin_service/current --setenv=DATABASE_URL=<URL> bash
> cd /work
> python3 manage.py db upgrade
> python3 manage.py auth create_admin --password 1111

python3 manage.py runserver -h 0.0.0.0 -p 5001 -d -r