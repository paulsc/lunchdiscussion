from ld.utils import CustomHandler
import logging
import cgi
from ld.models import Group, UserInfo
from google.appengine.api import users

class SignupHandler(CustomHandler):
	def get(self):
		context = {}
		self.render('signup', context)
		
	def error(self, message):
		context = { 'error_message': message }
		self.render('error', context)
		
	def post(self):
		group_shortname = cgi.escape(self.request.get('group_shortname'))
		
		if group_shortname == "":
			self.error("empty group name")
			return
		
		group = Group.gql("WHERE shortname=:1", group_shortname).get()
		
		if group != None:
			self.error("group name in use")
			return
			
		group_fullname = cgi.escape(self.request.get('group_fullname'))
		if group_fullname == "":
			context = { 'group_shortname': group_shortname }
			self.render("create_group", context)
			return
		
		current_user = users.get_current_user()
		userinfo = UserInfo.gql("WHERE user = :1", current_user).get()
		if userinfo == None:
			userinfo = UserInfo(user=current_user)
			userinfo.put()
		
		group = Group(shortname=group_shortname, fullname=group_fullname,
					  creator=userinfo)
		group.put()		
		userinfo.group = group
		userinfo.put()
		
		# work on proper template structure first
		if userinfo.nickname == "":
			self.redirect('/profile')
			return
		
		self.response.out.write('ok')
		
