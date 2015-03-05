import os
import sys

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

import tracker.views

db = SQLAlchemy(app)
