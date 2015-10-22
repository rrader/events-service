from fabric.api import run, settings, task, cd
from fabric.decorators import runs_once
from fabric.contrib.files import exists


REPO = 'https://github.com/rrader/events-service.git'
BASE_TARGET_PATH = '/opt'


@runs_once
def prepare_packages():
    run('apt-get update')


@task
def build_container(name):
    require_vagga()
    require_packages('git')

    build_path = get_build_path(name)

    run('rm -rf {}'.format(build_path))
    run('mkdir -p {}'.format(build_path))
    with cd(build_path):
        run('git clone {} .'.format(REPO))
        run('vagga _build {}'.format(name))
        rootfs = run('readlink -f .vagga/{}'.format(name))
        run('cp -R * .vagga/{}/work/'.format(name))
        run('tar zcf {}.tar.gz -C {} ./'.format(name, rootfs))


@task
def deploy_last_container(name):
    path = get_build_path(name)
    version = get_container_version(name) + 1
    target_path = '{}/{}/{}'.format(BASE_TARGET_PATH, name, version)
    current_path = '{}/{}/{}'.format(BASE_TARGET_PATH, name, 'current')

    if exists(target_path):
        run('rm -rf {}'.format(target_path))
    run('mkdir -p {}'.format(target_path))

    run('tar xf {}/{}.tar.gz -C {}'.format(path, name, target_path))
    run('rm -f {}'.format(current_path))
    run('ln -sf {} {}'.format(target_path, current_path))

    set_container_version(name, version)


@task
def deploy_container(name):
    build_container(name)
    deploy_last_container(name)


@task
def deploy():
    deploy_container('postgres')
    deploy_container('events_service')
    run('systemctl restart systemd-nspawn@postgres.service; sleep 3')
    run('systemctl restart systemd-nspawn@events_service.service')


def get_build_path(name):
    build_path = '/tmp/build/{}'.format(name)
    return build_path


def get_container_version(name):
    version_file = get_version_file(name)
    if not exists(version_file):
        return 0
    return int(run('cat {}'.format(version_file)))


def set_container_version(name, new_version):
    version_file = get_version_file(name)
    run('echo {} > {}'.format(new_version, version_file))


def get_version_file(name):
    version_file = '{}/{}.version'.format(BASE_TARGET_PATH, name)
    return version_file


def require_packages(*names):
    for name in names:
        with settings(warn_only=True):
            if run('dpkg -s {}'.format(name)).return_code != 0:
                prepare_packages()
                run('apt-get install -y {}'.format(name))


def require_vagga():
    with settings(warn_only=True):
        if run('which vagga').return_code != 0:
            require_packages('curl')
            run('curl http://files.zerogw.com/vagga/vagga-install.sh | sh')

# systemd-nspawn -D /opt/postgres/current/ --setenv=PGDATA=/data --bind=/opt/postgres/data:/data chown postgres:postgres -R /data
# systemd-nspawn -D /opt/postgres/current/ --setenv=PGDATA=/data --bind=/opt/postgres/data:/data su postgres -c '/usr/lib/postgresql/9.3/bin/pg_ctl initdb'
# systemd-nspawn -D /opt/postgres/current/ --setenv=PGDATA=/data --bind=/opt/postgres/data:/data su postgres -c '/usr/lib/postgresql/9.3/bin/postgres -h 127.0.0.1 -p 5433 -k /tmp -F'

# setup
# systemd-nspawn -D /opt/postgres/current/ --setenv=PGDATA=/data --bind=/opt/postgres/data:/data
# > su postgres -c '/usr/lib/postgresql/9.3/bin/postgres -h 127.0.0.1 -p 5433 -k /tmp -F' &
# > su postgres -c "/usr/lib/postgresql/9.3/bin/psql -h 127.0.0.1 -p 5433 -c \"CREATE USER user WITH PASSWORD 'pwd';\""
# > su postgres -c '/usr/lib/postgresql/9.3/bin/createdb -h 127.0.0.1 -p 5433 db -O user'

# Adding machine to systemd boot
# ln -s /opt/events_service/current /var/lib/machines/events_service
# systemctl enable systemd-nspawn@events_service.service
# systemctl edit --full systemd-nspawn@events_service.service
#   put proper command like
#     ExecStart=/usr/bin/systemd-nspawn --register=no --machine=%I --setenv=PGDATA=/data --bind=/opt/postgres/data:/data su postgres -c '/usr/lib/postgresql/9.3/bin/postgres -h 127.0.0.1 -p 5433-k /tmp -F'
#   or
#     systemd-nspawn -D /opt/events_service/current/ --register=no --setenv=DATABASE_URL=postgres://user:password@127.0.0.1:5433/db bash -c 'cd /work; alembic upgrade head'

# alembic
# ExecStartPre=/usr/bin/systemd-nspawn --register=no --machine=%I --setenv=DATABASE_URL=postgres://user:password@127.0.0.1:5433/db bash -c 'cd /work; alembic upgrade head'
# /usr/bin/systemd-nspawn --register=no --machine=%I --register=no --setenv=DATABASE_URL=postgres://user:password@127.0.0.1:5433/db bash -c 'cd /work; python3 manage.py run_server'
