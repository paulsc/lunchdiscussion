from google.appengine.ext import db

from datetime import date
from datetime import timedelta
from datetime import datetime

DEAD_LIMIT = 7

class Restaurant(db.Model):
	name = db.StringProperty()
	group = db.ReferenceProperty(collection_name='restaurants')
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
	group = db.ReferenceProperty(collection_name='users')	
	email = db.EmailProperty()
	nickname = db.StringProperty()
	avatar = db.BlobProperty()
	karma = db.IntegerProperty()
	lastvoted = db.DateProperty()
	lastposted = db.DateProperty()
	lunchcount = db.IntegerProperty()
	def voted_for_day(self, day):
		return self.lastvoted == day

def get_active_crew(group):
	one_week_ago = datetime.now() - timedelta(DEAD_LIMIT)
	return UserInfo.gql('WHERE lastposted >= DATE(:1, :2, :3) AND group = :4', 
				one_week_ago.year, one_week_ago.month, one_week_ago.day, group)

def get_dead_crew(group):
	one_week_ago = datetime.now() - timedelta(DEAD_LIMIT)
	return UserInfo.gql('WHERE lastposted < DATE(:1, :2, :3) AND group = :4', 
					one_week_ago.year, one_week_ago.month, one_week_ago.day, group)
		
GROUP_SHORTNAME_REGEXP = "\w{3,}"
class Group(db.Model):
	shortname = db.StringProperty()
	fullname = db.StringProperty()
	#address = db.TextProperty()
	creator = db.ReferenceProperty(UserInfo)
	created = db.DateProperty(auto_now_add=True)		

class Suggestion(db.Model):
	author = db.ReferenceProperty(UserInfo)
	group = db.ReferenceProperty(Group, collection_name='suggestions')
	restaurant = db.ReferenceProperty(Restaurant)
	date = db.DateProperty(auto_now_add=True)

	def ordered_comments(self):
		return self.comments.order('date')

	@staticmethod
	def get_for_day(date, group):
		return Suggestion.gql("WHERE date=DATE(:1, :2, :3) AND group = :4", 
							     date.year, date.month, date.day, group)

	@staticmethod
	def get_todays(group):
		return Suggestion.get_for_day(datetime.now(), group)

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
	rating = db.IntegerProperty()
	def pretty_rating(self):
		return [ 'very bad', 'bad', 'okay', 'good', 'FTW!!' ][self.rating + 2]

class ReplyTo(db.Model):
	uuid = db.StringProperty()
	user = db.ReferenceProperty(UserInfo)
	suggestion = db.ReferenceProperty(Suggestion)
	date = db.DateTimeProperty(auto_now_add=True)
	def __str__(self):
		return "%s@lunchdiscuss.appspotmail.com" % self.uuid
	
class InviteCode(db.Model):
	uuid = db.StringProperty()
	group = db.ReferenceProperty(Group)
	created = db.DateTimeProperty(auto_now_add=True)
	