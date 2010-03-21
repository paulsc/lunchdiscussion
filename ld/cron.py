import logging
from google.appengine.ext import webapp 
from google.appengine.ext import db

from datetime import datetime, timedelta
from models import ReplyTo

class DailyCronHandler(webapp.RequestHandler):
	def get(self):
		threshold = datetime.now() - timedelta(1)
		keys = ReplyTo.all().filter('date <', threshold)
		count = keys.count()
		db.delete(keys)
		logging.info("Daily cronjob: deleted %d ReplyTo entitite(s)." % count)