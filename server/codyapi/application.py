"""
application.py
- creates a Flask app instance and registers the database object
"""

from flask import Flask
from flask_cors import CORS

import sqlite3

import logging

def create_app(app_name='CODY_API'):
	#make logging configurations
	# general formating
	generalFormat = logging.Formatter(fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p')
	generalHandler = logging.FileHandler('cody.log')
	generalHandler.setFormatter(generalFormat)

	gen_log = logging.getLogger('general')
	gen_log.setLevel('INFO')
	gen_log.addHandler(generalHandler)

	# database tracking logging
	statsFormat = logging.Formatter(fmt = '%(asctime)s - %(message)s', datefmt = '%m/%d/%Y %I:%M:%S %p')
	statsHandler = logging.FileHandler('stats.log')
	statsHandler.setFormatter(statsFormat)

	stats_log = logging.getLogger('stats')
	stats_log.setLevel('INFO')
	stats_log.addHandler(statsHandler)

	gen_log.info('[Started new instance]')
	stats_log.info('[Started new stats instance]')


	app = Flask(app_name)
	app.config.from_object('codyapi.config.BaseConfig')

	cors = CORS(app, resources = {r"/api/*": {"origins": "*"}})

	#set db to WAL mode for multi-user support
	# with sqlite3.connect('annotations.db', isolation_level=None) as connection:
	# 	connection.execute('pragma journal_mode=wal')
	# 	cursor = connection.cursor()
	# 	cursor.execute('pragma journal_mode')
	# 	print(cursor.fetchone())

	from codyapi.api import api
	app.register_blueprint(api, url_prefix = "/api")

	from codyapi.models import db
	db.init_app(app)

	return app
