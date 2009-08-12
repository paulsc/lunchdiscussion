import os
import sys
import cgi
import logging
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import images
from datetime import datetime
from datetime import timedelta
from datetime import date
from tzinfo import Eastern

from models import *
from utils import *

class MainHandler(webapp.RequestHandler):
	def get(self):
		userinfo = UserInfo.current()
		if userinfo == None:
			self.redirect('/profile')
			return

		now = datetime.now()
		template_values = { 'now': now.strftime("%A %d/%m/%Y").lower(),
							'logout_url': users.create_logout_url('/'),
							'user': userinfo,
							'ask_to_rate' : ask_to_rate(),
							'active_crew': UserInfo.get_active_crew(),
							'dead_crew': UserInfo.get_dead_crew()
							}

		self.response.out.write(template.render('index.html', template_values))

class RestaurantHandler(webapp.RequestHandler):
	def get(self):
		new = cgi.escape(self.request.get('add'))
		if new != '':
			res = Restaurant(name=new.capitalize())
			res.put()

		template_values = { 'restaurants': Restaurant.all().order('name') }
		self.response.out.write(template.render('restaurants.html', template_values))

class SuggestionHandler(webapp.RequestHandler):
	def get(self):
		new = cgi.escape(self.request.get('add'))
		if new != '':
			userinfo = UserInfo.current()
			sug = Suggestion(restaurant=db.get(new), author=userinfo)
			notify_new_suggestion(sug)
			sug.put()
			
			userinfo.lastposted = date.today()
			userinfo.put()

		remove = cgi.escape(self.request.get('remove'))
		if remove != '':
			suggestion = db.get(remove)
			suggestion.delete()	

		now = datetime.now()
		suggestions = Suggestion.gql("WHERE date=DATE(:1, :2, :3)", 
				now.year, now.month, now.day)

		template_values = { 'suggestions': suggestions,
												'user': users.get_current_user() }
		self.response.out.write(template.render('suggestions.html', template_values))

	def post(self):
		text = cgi.escape(self.request.get('text'))
		suggestion = db.get(cgi.escape(self.request.get('suggestion')))
		notify_new_message(self.request.get('text'), suggestion)
		text = text.replace('\n', '<br/>')
		userinfo = UserInfo.current()
		comment = Comment(text=text, author=userinfo, suggestion=suggestion)
		comment.put()
		userinfo.lastposted = date.today()
		userinfo.put()
		self.get()

class ProfileHandler(webapp.RequestHandler):
	def get(self):
		userinfo = cgi.escape(self.request.get('user'))
		if userinfo != '':
			userinfo = db.get(userinfo)
			to_render = 'profile.html'
		else:
			userinfo = UserInfo.current()
			to_render = 'edit_profile.html'
	
		template_values = { 'userinfo': userinfo,
							'user': users.get_current_user() }
		self.response.out.write(template.render(to_render, template_values))

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

class AvatarHandler(webapp.RequestHandler):
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

class RatingHandler(webapp.RequestHandler):	
	def add_rating(self, suggestion, rating):
		userinfo = UserInfo.current()
		if userinfo.voted_for_day(suggestion.date):
			logging.error('user %s already voted for that day.' % userinfo.nickname)
			self.error(500)
			return
				
		restaurant = suggestion.restaurant
		rating = int(rating)
		if not rating in range(-2,3):
			logging.error('invalid rating received from user %s: %d' % (userinfo.nickname, rating))
			self.error(500)
			return
			
		restaurant.add_vote(rating)
		restaurant.put()
										
		author = suggestion.author
		author.karma = incr(author.karma, rating)
		author.put()
				
		userinfo = UserInfo.current()
		userinfo.lastvoted = suggestion.date
		userinfo.lunchcount = incr(userinfo.lunchcount)
		userinfo.put()
	
	def get(self):
		suggestion = self.request.get('suggestion')
		rating = self.request.get('rating')
		cancel = self.request.get('cancel')

		if cancel == 'true':
			userinfo = UserInfo.current()
			today = date.today()
			userinfo.lastvoted = today - timedelta(1) if is_morning() else today
			userinfo.put()
			self.response.out.write(template.render('thanks.html', None))
			return

		if suggestion != '' and rating != '':
			self.add_rating(db.get(suggestion), rating)
			self.response.out.write(template.render('thanks.html', None))
			return

			now = datetime.now(Eastern)

		if is_morning():
			day = datetime.now() - timedelta(1)
			day_title = "yesterday"
		else:
			day = datetime.now()
			day_title = "today"
		
		template_values = { 'day': day_title,
							'suggestions': Suggestion.get_for_day(day) }			
		self.response.out.write(template.render('rate.html', template_values))		

def main():
	userinfo = UserInfo.current()
	application = webapp.WSGIApplication([('/', MainHandler),
										  ('/profile', ProfileHandler),
										  ('/restaurants', RestaurantHandler),
										  ('/suggestions', SuggestionHandler),
										  ('/avatar', AvatarHandler),
										  ('/rate', RatingHandler)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
