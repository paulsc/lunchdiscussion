import os
import sys
import cgi
import time
import base64
import urllib
import urllib2
import logging
import wsgiref.handlers

from django.utils import simplejson as json
from google.appengine.api.urlfetch import fetch
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

YWSID = "wVUGQPPLapq5irwFfJFcFw"

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
		self.response.out.write(template.render('restaurants.html', 
												template_values))

class SuggestionHandler(webapp.RequestHandler):
	def get(self):
		new = cgi.escape(self.request.get('add'))
		userinfo = UserInfo.current()
		if new != '':
			sug = Suggestion(restaurant=db.get(new), author=userinfo)
			notify_new_suggestion(sug)
			sug.put()
			
			userinfo.lastposted = date.today()
			userinfo.put()

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
				logging.eror('user: %s tried to delete comment he doesn\'t own' % userinfo.nickname)

		now = datetime.now()
		suggestions = Suggestion.gql("WHERE date=DATE(:1, :2, :3)", 
				now.year, now.month, now.day)

		template_values = { 'suggestions': suggestions,
							'user': users.get_current_user() }
		self.response.out.write(template.render('suggestions.html', 
												template_values))

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
		
class RestaurantInfoHandler(webapp.RequestHandler):
	def get(self):
		restaurant = db.get(cgi.escape(self.request.get('restaurant')))
		template_values = { 'name': restaurant.name,
							'comments': restaurant.ordered_comments() }
		self.response.out.write(template.render('restaurant-info.html', template_values))

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
			self.response.out.write(template.render('thanks.html', None))
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
		self.response.out.write(template.render('thanks.html', None))

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
				
		template_values = { 'day': day.toordinal(),
							'day_title': day_title, 
							'restaurants': restaurants,
							'other_restaurants': other_restaurants }			
		self.response.out.write(template.render('rate.html', template_values))		

class StatsHandler(webapp.RequestHandler):
	def get(self):
		template_values = { 
			'karma_ranking': Restaurant.all().order('-karma').fetch(10),
			'lunchcount_ranking': Restaurant.all().order('-lunchcount').fetch(10),
			'best_user': UserInfo.all().order('-karma').fetch(5),
			'biggest_eater': UserInfo.all().order('-lunchcount').fetch(5)			
			}
							
		self.response.out.write(template.render('stats.html', template_values))

class SearchHandler(webapp.RequestHandler):
	def get(self):
		group = self.request.get('group')

		if group == '':
			res = template.render('search.html', { 'groups' : Group.all() })
			self.response.out.write(res)
			return
		
		group = db.get(group)
		
		address = urllib.quote_plus(group.address)
		url = "http://api.yelp.com/business_review_search?term=restaurant&location=%s&ywsid=%s&radius=1" % ( address, YWSID ) 
		response = fetch(url)
		if response.status_code != 200:
			logging.error('error making yelp api call')
			return
		
		results = obj = json.loads(response.content)
		template_values = { 'group': group, 'results': results }
		self.response.out.write(template.render('result.html', template_values))

class TwitterHandler(webapp.RequestHandler):
	def get_timeline(self):
		url = 'http://twitter.com/statuses/friends_timeline.json?count=6'
		req = urllib2.Request(url)
		auth = base64.encodestring('lunchdiscussr:1379zz')[:-1]
		req.add_header('Authorization', 'Basic %s' % auth)
		response = urllib2.urlopen(req)
		return json.loads(response.read())

	def get(self):
		try:
			timeline = self.get_timeline()
		except URLError:
			self.response.out.write('error loading twitter feed')
			return

		for status in timeline:
			time_struct = time.strptime(status['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
			date = datetime(*time_struct[:6])
			status['created_at'] = date
			logging.error('date: ' + str(date))
		context = { 'timeline': timeline }
		self.response.out.write(template.render('twitter.html', context))

def main():
	userinfo = UserInfo.current()
	application = webapp.WSGIApplication([('/', MainHandler),
										  ('/profile', ProfileHandler),
										  ('/restaurant-info', RestaurantInfoHandler),
										  ('/restaurants', RestaurantHandler),
										  ('/suggestions', SuggestionHandler),
										  ('/avatar', AvatarHandler),
										  ('/rate', RatingHandler),
										  ('/search', SearchHandler), 
											('/twitter', TwitterHandler),
										  ('/stats', StatsHandler)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
