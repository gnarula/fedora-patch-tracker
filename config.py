import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'app.db')

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
