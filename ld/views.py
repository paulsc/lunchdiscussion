import cgi
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images

from datetime import datetime, date, timedelta

from utils import TemplateHelperHandler, incr, is_morning,\
    notify_suggestion, post_comment

from models import UserInfo, Suggestion, Restaurant, RestaurantComment
from ld.models import get_active_crew, get_dead_crew
from ld.utils import LDContextHandler, can_vote, authorize_group

class IndexHandler(LDContextHandler):
	def get(self):
		if self.currentuser == None or self.currentuser.grouprefs.count() == 0:
			self.redirect('/signup')
			return

		if self.currentuser.nickname == "":
			self.redirect('/profile')
			return

		firstgroup = self.currentuser.grouprefs.get().group
		self.redirect('/' + firstgroup.shortname)
		
class HomeHandler(LDContextHandler):
	@authorize_group
	def get(self):
		group = self.currentgroup
		
		context = { 'ask_to_rate' : can_vote(self.currentuser, self.currentgroup),
					'active_crew': get_active_crew(group),
					'dead_crew': get_dead_crew(group), 
					'suggestions': Suggestion.get_todays(group),
					'restaurants': Restaurant.get_for_group(group) }

		self.render('home', context)

class RestaurantHandler(LDContextHandler):
	@authorize_group
	def get(self):
		context = { 'restaurants': Restaurant.get_for_group(self.currentgroup) }
		self.render_plain('restaurants', context)

	@authorize_group
	def post(self):
		name = cgi.escape(self.request.get('name'))
		name = name.capitalize()
		if name == '':
			self.error(400)
			return
			
		restaurant = Restaurant.gql("WHERE name = :1 AND group = :2", name, self.currentgroup).get()
		if restaurant == None:
			restaurant = Restaurant(name=name, group=self.currentgroup)
			restaurant.put()
		else:
			logging.info("restaurant '%s' already exists, skipping" % name)

		self.get()

class SuggestionHandler(LDContextHandler):
	@authorize_group
	def get(self):
		context = { 'suggestions': Suggestion.get_todays(self.currentgroup) }
		self.render('suggestions', context)

	@authorize_group
	def post(self):
		action = cgi.escape(self.request.get('action'))
		
		if action == 'add_suggestion':
			restaurant = cgi.escape(self.request.get('restaurant'))
			if restaurant == '':
				self.error(400)
				return

			sug = Suggestion(restaurant=db.get(restaurant), author=self.currentuser, 
							 group=self.currentgroup)
			sug.put()
			self.currentuser.lastposted = date.today()
			self.currentuser.put()
			notify_suggestion(sug)
			
		elif action == "remove_suggestion":
			suggestion = cgi.escape(self.request.get('suggestion'))
			suggestion = db.get(suggestion)
			if suggestion.author.user == self.currentuser.user:
				suggestion.delete()	
			else:
				logging.error('user: %s tried to delete suggestion he doesn\'t own' % self.currentuser.nickname)

		elif action == "add_comment":
			text = cgi.escape(self.request.get('text'))
			suggestion = db.get(cgi.escape(self.request.get('suggestion')))
			post_comment(text, self.currentuser, suggestion)
			
		elif action == "remove_comment":
			comment = cgi.escape(self.request.get('comment'))
			comment = db.get(comment)
			if comment.author.user == self.currentuser.user:
				comment.delete()
			else:
				logging.error('user: %s tried to delete comment he doesn\'t own' % self.currentuser.nickname)

		else:
			self.error(400)
			return
		
		self.get()

class ProfileHandler(LDContextHandler):
	def get(self):
		userinfo = cgi.escape(self.request.get('user'))
		if userinfo != '':
			self.render('profile', { 'userinfo': db.get(userinfo) })
		else:
			self.render_edit()

	def render_edit(self, notification=None):
		context = { 'userinfo': self.currentuser, 'user': users.get_current_user( )}
		self.render('edit_profile', context, notification=notification)

	def post(self):
		userinfo = self.currentuser
		if userinfo == None:
			userinfo = UserInfo()
		
		userinfo.nickname = cgi.escape(self.request.get('nickname'))
		if userinfo.nickname == "":
			self.render_edit("nickname can't be empty")
			return
		
		email = cgi.escape(self.request.get('email'))
		avatar = self.request.get('avatar')
		first_login = self.request.get('first_login')
		if avatar != '':
			avatar = images.resize(avatar, 128)
			userinfo.avatar = db.Blob(avatar)
		if email == '':
			email = 'none'
		userinfo.email = email

		if first_login != '':
			userinfo.lastposted = date.today()
			userinfo.lastvoted = date.today()
			
		userinfo.put()
		self.redirect('/')
		
class RestaurantInfoHandler(LDContextHandler):
	@authorize_group
	def get(self):
		restaurant = db.get(cgi.escape(self.request.get('restaurant')))
		context = { 'name': restaurant.name,
							'comments': restaurant.ordered_comments() }
		self.render('restaurant-info', context)

class AvatarHandler(LDContextHandler):
	def get(self):
		userkey = self.request.get("user")
		if userkey == '':
			userinfo = self.currentuser
		else:
			userinfo = db.get(userkey)

		if userinfo.avatar:
			self.response.headers['Content-Type'] = "image/png"
			self.response.out.write(userinfo.avatar)
		else:
			self.error(404)

class RatingHandler(LDContextHandler):	
	def add_rating(self, date, restaurant, author, rating):
		if self.currentuser.voted_for_day(date):
			logging.error('user %s already voted for that day.' 
							% self.currentuser.nickname)
			self.error(500)
			return
		
		if not rating in range(-2,3):
			logging.error('invalid rating received from user %s: %d' 
							% (self.currentuser.nickname, rating))
			self.error(500)
			return
			
		restaurant.add_vote(rating)
		restaurant.put()
						
		if author:
			author.karma = incr(author.karma, rating)
			author.put()
				
		self.currentuser.lastvoted = date
		self.currentuser.lunchcount = incr(self.currentuser.lunchcount)
		self.currentuser.put()

	@authorize_group
	def post(self):
		cancel = self.request.get('cancel')
		day = date.fromordinal(int(self.request.get('day')))
		
		if cancel == 'true':
			self.currentuser.lastvoted = day
			self.currentuser.put()
			self.render('thanks')
			return

		rating = int(self.request.get('rating'))

		restaurant = cgi.escape(self.request.get('restaurant'))
		
		if restaurant == "other":
			restaurant = cgi.escape(self.request.get('others'))
				
		suggestion = Suggestion.find(day, restaurant)
		author = suggestion.author if suggestion else None

		restaurant=db.get(restaurant)
		comment = cgi.escape(self.request.get('comment'))
		if comment != "":
			comment = comment.replace('\n', '<br/>')	
			comment = RestaurantComment(text=comment, restaurant=restaurant,
						author=self.currentuser, rating=rating)
			comment.put()

		self.add_rating(day, restaurant, author, rating)
		self.render_plain('thanks')

	@authorize_group
	def get(self):
		if is_morning():
			day = datetime.now() - timedelta(1)
			day_title = "yesterday"
		else:
			day = datetime.now()
			day_title = "today"
		
		suggestions = Suggestion.get_for_day(day, self.currentgroup)
		restaurants = [ s.restaurant for s in suggestions ]
		res_keys = [ r.key() for r in restaurants ]

		other_restaurants = []
		all_restaurants = Restaurant.all().order('name')
		for res in all_restaurants:
			if res.key() not in res_keys:
				other_restaurants.append(res)
				
		context = { 'day': day.toordinal(),
					'day_title': day_title, 
					'restaurants': restaurants,
					'other_restaurants': other_restaurants }			
		self.render('rate', context)		

class StatsHandler(TemplateHelperHandler):
	def get(self):
		context = { 
			'karma_ranking': Restaurant.all().order('-karma').fetch(10),
			'lunchcount_ranking': Restaurant.all().order('-lunchcount').fetch(10),
			'best_user': UserInfo.all().order('-karma').fetch(5),
			'biggest_eater': UserInfo.all().order('-lunchcount').fetch(5)			
			}
							
		self.render('stats', context)
