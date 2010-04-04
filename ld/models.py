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
	
	@classmethod
	def get_for_group(cls, group):
		return cls.gql("WHERE group=:1 ORDER BY name", group)

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

def _get_crew_helper(group, compare):
	def is_empty(str): 
		return str == "" or str == None	
	one_week_ago = datetime.now().date() - timedelta(DEAD_LIMIT)
	f = lambda user: (not is_empty(user.nickname)) and compare(user, one_week_ago)
	users = [ ref.user for ref in group.userrefs ]
	return filter(f, users)
	
def get_active_crew(group):
	compare = lambda user, date: user.lastposted >= date
	return _get_crew_helper(group, compare)
	
def get_dead_crew(group):
	compare = lambda user, date: user.lastposted < date
	return _get_crew_helper(group, compare)
		
RE_GROUPNAME = "\w{3,}"
class Group(db.Model):
	shortname = db.StringProperty()
	fullname = db.StringProperty()
	#address = db.TextProperty()
	creator = db.ReferenceProperty(UserInfo)
	created = db.DateProperty(auto_now_add=True)		
	
	def get_best_users(self):
		users = [ ref.user for ref in self.userrefs ]
		compare = lambda x, y: cmp(y.karma, x.karma)
		users.sort(compare)
		return users[:5]
	
	def get_biggest_users(self):
		users = [ ref.user for ref in self.userrefs ]
		compare = lambda x, y: cmp(y.lunchcount, x.lunchcount)
		users.sort(compare)
		return users[:5]
	
class GroupUserInfo(db.Model):
	group = db.ReferenceProperty(Group, required=True, collection_name='userrefs')
	user = db.ReferenceProperty(UserInfo, required=True, collection_name='grouprefs')
	groupname = db.StringProperty(required=True) # for quick access

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
	