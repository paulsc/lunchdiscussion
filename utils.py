import os
import uuid

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from datetime import datetime, date, timedelta
from tzinfo import Eastern

from models import UserInfo, Suggestion, Comment, ReplyTo
from google.appengine.api import mail

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
		
def post_comment(text, author, suggestion):
	brtext = text.replace('\n', '<br/>')
	comment = Comment(text=brtext, author=author, suggestion=suggestion)
	comment.put()
	author.lastposted = date.today()
	author.put()
	notify_new_comment(text, comment)

# following 3 functions need cleaning up
def send_notification(message, suggestion, exclude_user):
	def f(i): 
		return i.nickname != "" and i.user != exclude_user and i.email != 'none'
	targets = filter(f, UserInfo.get_active_crew())
	#targets = UserInfo.gql('WHERE nickname = :1', 'paul')

	def send_to_target(target):
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "Lunchdiscussion.com update"
		email.body = "www.lunchdiscussion.com update\n" + message
		email.to = "%s <%s>" % (target.nickname, target.email)
		reply_to = ReplyTo(user=target, suggestion=suggestion, uuid=uuid.uuid4().hex)
		email.reply_to = str(reply_to)
		email.send()
		reply_to.put()
	
	map(send_to_target, targets)
	
def notify_new_comment(text, comment):
	body = "On '%s'\n%s: %s" % (comment.suggestion.restaurant.name, 
								comment.author.nickname, text)
	send_notification(body, comment.suggestion, comment.author.user)

def notify_new_suggestion(suggestion):
	body = "%s suggests going to '%s' for lunch." % \
			(suggestion.author.nickname, suggestion.restaurant.name)
	send_notification(body, suggestion, suggestion.author.user)		
	
