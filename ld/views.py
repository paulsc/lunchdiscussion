import cgi
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images

from datetime import datetime, date, timedelta

from utils import CustomHandler, incr, ask_to_rate, is_morning,\
    notify_suggestion, post_comment

from models import UserInfo, Suggestion, Restaurant, RestaurantComment

class MainHandler(CustomHandler):
	def get(self):
		userinfo = UserInfo.current()
		if userinfo == None:
			self.redirect('/signup')
			return

		if userinfo.nickname == "":
			self.redirect('/profile')
			return

		context = { 'logout_url': users.create_logout_url('/'),
					'userinfo': userinfo,
					'ask_to_rate' : ask_to_rate(),
					'active_crew': UserInfo.get_active_crew(),
					'dead_crew': UserInfo.get_dead_crew(), 
					'suggestions': Suggestion.get_todays(),
					'restaurants': Restaurant.all().order('name'),
					}

		self.render('index', context)

class RestaurantHandler(CustomHandler):
	def get(self):
		new = cgi.escape(self.request.get('add'))
		if new != '':
			res = Restaurant(name=new.capitalize())
			res.put()

		context = { 'restaurants': Restaurant.all().order('name') }
		self.render('restaurants', context)

class SuggestionHandler(CustomHandler):
	def get(self):
		new = cgi.escape(self.request.get('add'))
		userinfo = UserInfo.current()
		if new != '':
			sug = Suggestion(restaurant=db.get(new), author=userinfo)
			sug.put()
			userinfo.lastposted = date.today()
			userinfo.put()
			notify_suggestion(sug)

		remove = cgi.escape(self.request.get('remove'))
		if remove != '':
			suggestion = db.get(remove)
			if suggestion.author.user == userinfo.user:
				suggestion.delete()	
			else:
				logging.error('user: %s tried to delete suggestion he doesn\'t own' % userinfo.nickname)

		remove_comment = cgi.escape(self.request.get('remove_comment'))
		if remove_comment != '':
			comment = db.get(remove_comment)
			if comment.author.user == userinfo.user:
				comment.delete()
			else:
				logging.error('user: %s tried to delete comment he doesn\'t own' % userinfo.nickname)

		context = { 'suggestions': Suggestion.get_todays(), 
					'userinfo': userinfo }

		self.render('suggestions', context)

	def post(self):
		text = cgi.escape(self.request.get('text'))
		suggestion = db.get(cgi.escape(self.request.get('suggestion')))
		userinfo = UserInfo.current()
		post_comment(text, userinfo, suggestion)
		self.get()

class ProfileHandler(CustomHandler):
	def get(self):
		userinfo = cgi.escape(self.request.get('user'))
		if userinfo != '':
			userinfo = db.get(userinfo)
			to_render = 'profile'
		else:
			userinfo = UserInfo.current()
			to_render = 'edit_profile'
	
		context = { 'userinfo': userinfo, 'user': users.get_current_user() }
		self.render(to_render, context)

	def post(self):
		userinfo = UserInfo.current()
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
		
class RestaurantInfoHandler(CustomHandler):
	def get(self):
		restaurant = db.get(cgi.escape(self.request.get('restaurant')))
		context = { 'name': restaurant.name,
							'comments': restaurant.ordered_comments() }
		self.render('restaurant-info', context)

class AvatarHandler(CustomHandler):
	def get(self):
		userkey = self.request.get("user")
		if userkey == '':
			userinfo = UserInfo.current()
		else:
			userinfo = db.get(userkey)

		if userinfo.avatar:
			self.response.headers['Content-Type'] = "image/png"
			self.response.out.write(userinfo.avatar)
		else:
			self.error(404)

class RatingHandler(CustomHandler):	
	def add_rating(self, date, restaurant, author, rating):
		userinfo = UserInfo.current()
		if userinfo.voted_for_day(date):
			logging.error('user %s already voted for that day.' 
							% userinfo.nickname)
			self.error(500)
			return
		
		if not rating in range(-2,3):
			logging.error('invalid rating received from user %s: %d' 
							% (userinfo.nickname, rating))
			self.error(500)
			return
			
		restaurant.add_vote(rating)
		restaurant.put()
						
		if author:
			author.karma = incr(author.karma, rating)
			author.put()
				
		userinfo = UserInfo.current()
		userinfo.lastvoted = date
		userinfo.lunchcount = incr(userinfo.lunchcount)
		userinfo.put()
	
	def post(self):
		cancel = self.request.get('cancel')
		day = date.fromordinal(int(self.request.get('day')))
		
		if cancel == 'true':
			userinfo = UserInfo.current()
			userinfo.lastvoted = day
			userinfo.put()
			self.render('thanks', None)
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
						author=UserInfo.current(), rating=rating)
			comment.put()

		self.add_rating(day, restaurant, author, rating)
		self.render('thanks', None)

	def get(self):
		if is_morning():
			day = datetime.now() - timedelta(1)
			day_title = "yesterday"
		else:
			day = datetime.now()
			day_title = "today"
		
		suggestions = Suggestion.get_for_day(day)
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

class StatsHandler(CustomHandler):
	def get(self):
		context = { 
			'karma_ranking': Restaurant.all().order('-karma').fetch(10),
			'lunchcount_ranking': Restaurant.all().order('-lunchcount').fetch(10),
			'best_user': UserInfo.all().order('-karma').fetch(5),
			'biggest_eater': UserInfo.all().order('-lunchcount').fetch(5)			
			}
							
		self.render('stats', context)
