import cgi
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images

from datetime import datetime, date, timedelta

from utils import TemplateHelperHandler, incr, is_morning,\
    notify_suggestion, post_comment

from models import UserInfo, Suggestion, Restaurant, RestaurantComment
from ld.models import Group, get_active_crew, get_dead_crew
from ld.utils import LDContextHandler, can_vote

class IndexHandler(LDContextHandler):
	def get(self):
		if self.currentuser == None or self.currentgroup == None:
			self.redirect('/signup')
			return

		if self.currentuser.nickname == "":
			self.redirect('/profile')
			return

		if self.currentuser.group == None:
			self.redirect('/signup')
			return

		self.redirect('/' + self.currentuser.group.shortname)
		
class HomeHandler(LDContextHandler):
	def get(self):
		if self.currentuser == None or self.currentuser.group == None:
			self.redirect('/')
			return
		
		group_shortname = self.request.path.strip('/')
		group = Group.gql('WHERE shortname = :1', group_shortname).get()
		if group == None:
			self.response.out.write('group not found')
			return
		
		if self.currentuser.group.key() != group.key():
			self.render('request_invite', { 'notification': "not a member of this group" })
			return
		
		context = { 'logout_url': users.create_logout_url('/test'),
					'ask_to_rate' : can_vote(self.currentuser),
					'active_crew': get_active_crew(self.currentgroup),
					'dead_crew': get_dead_crew(self.currentgroup), 
					'suggestions': Suggestion.get_todays(self.currentgroup),
					'restaurants': Restaurant.gql("WHERE group = :1 ORDER by name", group) }

		self.render('home', context)		
		

class RestaurantHandler(LDContextHandler):
	def get(self):
		name = cgi.escape(self.request.get('add'))
		name = name.capitalize()

		if name != '':
			restaurant = Restaurant.gql("WHERE name = :1 AND group = :2", name, self.currentuser.group).get()
			if restaurant == None:
				restaurant = Restaurant(name=name, group=self.currentuser.group)
				restaurant.put()
		
		restaurants = Restaurant.gql("WHERE group = :1 ORDER by name", self.currentuser.group)
		context = { 'restaurants': restaurants }
		self.render('restaurants', context)

class SuggestionHandler(LDContextHandler):
	def get(self):
		new = cgi.escape(self.request.get('add'))
		if new != '':
			sug = Suggestion(restaurant=db.get(new), author=self.currentuser, 
							 group=self.currentgroup)
			sug.put()
			self.currentuser.lastposted = date.today()
			self.currentuser.put()
			notify_suggestion(sug)

		remove = cgi.escape(self.request.get('remove'))
		if remove != '':
			suggestion = db.get(remove)
			if suggestion.author.user == self.currentuser.user:
				suggestion.delete()	
			else:
				logging.error('user: %s tried to delete suggestion he doesn\'t own' % self.currentuser.nickname)

		remove_comment = cgi.escape(self.request.get('remove_comment'))
		if remove_comment != '':
			comment = db.get(remove_comment)
			if comment.author.user == self.currentuser.user:
				comment.delete()
			else:
				logging.error('user: %s tried to delete comment he doesn\'t own' % self.currentuser.nickname)

		context = { 'suggestions': Suggestion.get_todays(self.currentgroup), 
					'userinfo': self.currentuser }

		self.render('suggestions', context)

	def post(self):
		text = cgi.escape(self.request.get('text'))
		suggestion = db.get(cgi.escape(self.request.get('suggestion')))
		post_comment(text, self.currentuser, suggestion)
		self.get()

class ProfileHandler(LDContextHandler):
	def get(self):
		userinfo = cgi.escape(self.request.get('user'))
		if userinfo != '':
			userinfo = db.get(userinfo)
			to_render = 'profile'
		else:
			userinfo = self.currentuser
			to_render = 'edit_profile'
	
		context = { 'userinfo': userinfo, 'user': users.get_current_user() }
		self.render(to_render, context)

	def post(self):
		userinfo = self.currentuser
		if userinfo == None:
			userinfo = UserInfo()
		userinfo.nickname = cgi.escape(self.request.get('nickname'))
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
		
class RestaurantInfoHandler(TemplateHelperHandler):
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
		self.render('thanks')

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
