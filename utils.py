import os

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from datetime import datetime
from datetime import date
from datetime import timedelta
from tzinfo import Eastern

from models import UserInfo, Suggestion, ReplyTo

import logging

class CustomHandler(webapp.RequestHandler):
	def render(self, template_name, context):
		path = os.path.join(os.path.dirname(__file__), 
				'templates', '%s.html' % template_name) 
		self.response.out.write(template.render(path, context))

def incr(var, val = 1): return 1 if var == None else var + val

def is_morning():
	now = datetime.now(Eastern)
	return now.hour < 14
	
def ask_to_rate():
	today = date.today()
	yesterday = today - timedelta(1)
	userinfo = UserInfo.current()
	if is_morning():
		return (not userinfo.voted_for_day(yesterday) 
				and Suggestion.get_for_day(yesterday).count() > 0)
	else:
		return (not userinfo.voted_for_day(today) 
				and Suggestion.get_for_day(today).count() > 0)
		
def send_notification(message, suggestion):
	currentuser = users.get_current_user()
	def f(i): 
		return i.nickname != "" and i.user != currentuser and i.email != 'none'
	targets = filter(f, UserInfo.get_active_crew())

	def send_to_target(target):
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "Lunchdiscussion.com update"
		email.body = "lunchdiscussion.com update\n " + message
		email.to = "%s <%s>" % (target.nickname, target.email)
		email.to = "paul <paul167@gmail.com"
		reply_to = ReplyTo(user=target, suggestion=suggestion)
		email.reply_to = str(reply_to)
		email.send()
		reply_to.put()
	
	map(send_to_target, targets)
	
def notify_new_message(comment, suggestion):
	body = "On '%s'\n%s: %s" % (suggestion.restaurant.name, 
								UserInfo.current().nickname, comment)
	send_notification(body, suggestion)

def notify_new_suggestion(suggestion):
	body = "%s suggests going to '%s' for lunch." % \
			(UserInfo.current().nickname, suggestion.restaurant.name)
	send_notification(body, suggestion)		
