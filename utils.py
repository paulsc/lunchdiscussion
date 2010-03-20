import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api.labs import taskqueue

from datetime import datetime, date, timedelta
from tzinfo import Eastern

from models import UserInfo, Suggestion, Comment, ReplyTo

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
	taskqueue.add(url='/emailtask', params={'comment': comment.key()})

