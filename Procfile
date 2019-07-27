web: gunicorn app:app --daemon
init: python manage.py db init
migrate: python manage.py db migrate
upgrade: python manage.py db upgrade
worker: python worker.py&
