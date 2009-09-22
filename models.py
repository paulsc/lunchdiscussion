from google.appengine.ext import db
from google.appengine.api import users

from datetime import date
from datetime import timedelta
from datetime import datetime

DEAD_LIMIT = 7

class Restaurant(db.Model):
	name = db.StringProperty()
	karma = db.IntegerProperty()
	lunchcount = db.IntegerProperty()
	lastlunched = db.DateProperty()
	def add_vote(self, karma):
		self.karma = self.karma + karma if self.karma else karma
		self.lunchcount = self.lunchcount + 1 if self.lunchcount else 1
		self.lastlunched = date.today()
	def ordered_comments(self):
		return self.comments.order('date').fetch(10)
	def has_comments(self):
		return self.comments.count() > 0

class UserInfo(db.Model):
	user = db.UserProperty(auto_current_user_add=True)
	email = db.EmailProperty()
	nickname = db.StringProperty()
	avatar = db.BlobProperty()
	karma = db.IntegerProperty()
	lastvoted = db.DateProperty()
	lastposted = db.DateProperty()
	lunchcount = db.IntegerProperty()
	def voted_for_day(self, day):
		return self.lastvoted == day
	@staticmethod
	def current():
		return UserInfo.gql("WHERE user = :1", users.get_current_user()).get()
	@staticmethod
	def get_active_crew():
		one_week_ago = datetime.now() - timedelta(DEAD_LIMIT)
		return UserInfo.gql('WHERE lastposted >= DATE(:1, :2, :3)', 
					one_week_ago.year, one_week_ago.month, one_week_ago.day)
	@staticmethod
	def get_dead_crew():
		one_week_ago = datetime.now() - timedelta(DEAD_LIMIT)
		return UserInfo.gql('WHERE lastposted < DATE(:1, :2, :3)', 
						one_week_ago.year, one_week_ago.month, one_week_ago.day)			

class Suggestion(db.Model):
	author = db.ReferenceProperty(UserInfo)
	restaurant = db.ReferenceProperty(Restaurant)
	date = db.DateProperty(auto_now_add=True)
	def ordered_comments(self):
		return self.comments.order('date')
	@staticmethod
	def get_for_day(date):
		return Suggestion.gql("WHERE date=DATE(:1, :2, :3)", date.year, 
								date.month, date.day)
	@staticmethod
	def find(date, restaurant_key):
		return Suggestion.gql("WHERE date=DATE(:1, :2, :3) AND restaurant = \
				KEY(:4)", date.year, date.month, date.day, restaurant_key).get()

class Comment(db.Model):
	suggestion = db.ReferenceProperty(Suggestion, collection_name='comments')
	text = db.TextProperty()
	author = db.ReferenceProperty(UserInfo)
	date = db.DateTimeProperty(auto_now_add=True)

class RestaurantComment(db.Model):
	restaurant = db.ReferenceProperty(Restaurant, collection_name='comments')
	text = db.TextProperty()
	author = db.ReferenceProperty(UserInfo)
	date = db.DateTimeProperty(auto_now_add=True)