from google.appengine.api import users
from ld.models import Group, UserInfo, GROUP_SHORTNAME_REGEXP, GroupUserInfo
from ld.utils import is_empty, LDContextHandler
import cgi
import re

class SignupHandler(LDContextHandler):
	def get(self):
		if self.currentuser != None and self.currentgroup != None:
			self.redirect("/" + self.currentgroup.shortname)
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
		
		userinfo = self.currentuser
		if userinfo == None:
			userinfo = UserInfo(user=users.get_current_user())
			userinfo.put()
		
		group = Group(shortname=group_shortname, fullname=group_fullname,
					  creator=userinfo)
		group.put()		
		
		relationship = GroupUserInfo(group=group, user=userinfo)
		relationship.put()
		
		if is_empty(userinfo.nickname):
			self.render('edit_profile')
			return
		
		self.redirect("/")
