from ld.utils import TemplateHelperHandler, is_empty
import logging
import cgi
from ld.models import Group, UserInfo, GROUP_SHORTNAME_REGEXP
from google.appengine.api import users
import re

class SignupHandler(TemplateHelperHandler):
	def get(self):
		userinfo = UserInfo.current()
		if userinfo != None and userinfo.group != None:
			self.redirect("/" + userinfo.group.shortname)
			return
		
		self.render('signup')
		
	def error(self, message):
		context = { 'notification': message }
		self.render('signup', context)
		
	def post(self):
		group_shortname = cgi.escape(self.request.get('group_shortname'))
		
		if re.match(GROUP_SHORTNAME_REGEXP, group_shortname) == None:
			self.error("groups short name has to be alphanumeric with "
					   "underscores and at least 3 characters long")
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
		
		if is_empty(userinfo.nickname):
			self.render('edit_profile')
			return
		
		self.redirect("/")
