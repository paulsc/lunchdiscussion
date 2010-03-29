import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api.labs import taskqueue

from datetime import datetime, date, timedelta
from timezone import Eastern

from models import UserInfo, Suggestion, Comment
from google.appengine.api import users
from ld.models import get_active_crew, Group
from functools import wraps

class TemplateHelperHandler(webapp.RequestHandler):
	def render(self, template_name, context = None):
		path = os.path.join(os.path.dirname(__file__), '..',
				'templates', '%s.html' % template_name) 
		self.response.out.write(template.render(path, context))
		
class LDContextHandler(TemplateHelperHandler):
	def initialize(self, request, response):
		self.currentuser = UserInfo.gql("WHERE user = :1", users.get_current_user()).get()
		path = request.path.lstrip('/')
		slashindex = path.find('/')
		if slashindex == -1:
			groupname = path
		else:
			groupname = path[:slashindex]
		self.currentgroup = Group.gql("WHERE shortname = :1", groupname).get()
		
		super(LDContextHandler, self).initialize(request, response)

	def render(self, template_name, context = None, notification=None):
		if context == None:
			context = {}
		context['currentuser'] = self.currentuser
		context['currentgroup'] = self.currentgroup
		context['logout_url'] = users.create_logout_url('/')
		if notification != None:
			context['notification'] = notification
		
		super(LDContextHandler, self).render(template_name, context)
		
	def render_plain(self, template_name, context=None):
		super(LDContextHandler, self).render(template_name, context)
		
def authorize_group(f):
	@wraps(f)
	def wrapper(self, *args, **kwds):
		if self.currentgroup == None:
			self.error(404)
			return

		if self.currentuser == None:
			self.redirect('/signup')
			return

		grouprefs = self.currentuser.grouprefs
		result = grouprefs.filter('groupname =', self.currentgroup.shortname).get()
		if result == None: # user is not a member of this group
			self.render('request_invite', notification="not a member of this group")
			return
		
		return f(self, *args, **kwds)
	return wrapper

		
def incr(var, val = 1): 
	return val if var == None else var + val

def is_empty(str): 
	return str == "" or str == None	

def is_morning():
	now = datetime.now(Eastern)
	return now.hour < 14
	
def can_vote(userinfo, group):
	def can_vote_for_day(day):
		return (not userinfo.voted_for_day(day)
			    and Suggestion.get_for_day(day, group).count() > 0)
	
	if is_morning():
		return can_vote_for_day(date.today() - timedelta(1))
	else:
		return can_vote_for_day(date.today())
	
		
def post_comment(text, author, suggestion):
	brtext = text.replace('\n', '<br/>')
	comment = Comment(text=brtext, author=author, suggestion=suggestion)
	comment.put()
	author.lastposted = date.today()
	author.put()
	notify_comment(text, comment)

# following 3 functions need cleaning up
def send_notification(message, suggestion, exclude_user):
	def f(i): 
		return i.nickname != "" and i.user != exclude_user and i.email != 'none'
	targets = filter(f, get_active_crew(suggestion.group))
	#targets = UserInfo.gql('WHERE nickname = :1', 'paul')
	
	params = { 'suggestion': suggestion.key(), 'message': message }
	for target in targets:
		params['target'] = target.key()
		taskqueue.add(url='/emailtask', params=params)

def notify_comment(text, comment):
	body = "On '%s'\n%s: %s" % (comment.suggestion.restaurant.name, 
								comment.author.nickname, text)
	send_notification(body, comment.suggestion, comment.author.user)

def notify_suggestion(suggestion):
	body = "%s suggests going to '%s' for lunch." % \
			(suggestion.author.nickname, suggestion.restaurant.name)
	send_notification(body, suggestion, suggestion.author.user)		
	
