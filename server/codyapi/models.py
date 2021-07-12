"""
models.py
- Data classes for the surveyapi application
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import traceback

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User():
	def __init__(self, email, password):
		self.email = email
		self.password = generate_password_hash(password, method="sha256")

	@classmethod
	def authenticate(cls, **kwargs):
		email = kwargs.get('email')
		password = kwargs.get('password')

		if not email or not password:
			return None

		#get user from db
		try:
			call = db.session.execute(
				"SELECT id, password FROM users WHERE email = :mail",
				{"mail": email})
			user = call.fetchone()
			db.session.commit()

		except:
			print("Error with accessing db to authenticate user in models.py:", traceback.format_exc())

		#user[0] = id, user[1] = password
		db_password = user[1] if user is not None else ''
		if not user or not check_password_hash(db_password, password):
			return None

		return {'id': user[0], 'email': email}

	def to_dict(self):
		return dict(email = self.email)