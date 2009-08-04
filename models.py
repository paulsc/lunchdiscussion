from google.appengine.ext import db
from datetime import date
from datetime import timedelta

class Restaurant(db.Model):
	name = db.StringProperty()
	karma = db.IntegerProperty()
	
	def add_karma(self, karma):
		if self.karma == None:
			self.karma = karma
		else:
			self.karma += karma

class UserInfo(db.Model):
	user = db.UserProperty(auto_current_user_add=True)
	email = db.EmailProperty()
	nickname = db.StringProperty()
	avatar = db.BlobProperty()
	karma = db.IntegerProperty()
	lastvoted = db.DateProperty()
	lastposted = db.DateProperty()

	def voted_for_day(self, day):
		return self.lastvoted == day

	def add_karma(self, karma):
		if self.karma == None:
			self.karma = karma
		else:
			self.karma += karma		

class Suggestion(db.Model):
	author = db.ReferenceProperty(UserInfo)
	restaurant = db.ReferenceProperty(Restaurant)
	date = db.DateProperty(auto_now_add=True)
	def ordered_comments(self):
		return self.comments.order('date')

class Comment(db.Model):
	suggestion = db.ReferenceProperty(Suggestion, collection_name='comments')
	text = db.TextProperty()
	author = db.ReferenceProperty(UserInfo)
	date = db.DateTimeProperty(auto_now_add=True)
