import redis

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from rq import Queue

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

conn = redis.from_url(app.config['REDIS_URL'])
q = Queue(connection=conn)

import tracker.views
