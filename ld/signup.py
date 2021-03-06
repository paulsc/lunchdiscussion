from google.appengine.api import users
from ld.models import Group, UserInfo, RE_GROUPNAME, GroupUserInfo
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
		
		if re.match(RE_GROUPNAME, group_shortname) == None:
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
			userinfo = UserInfo()
			userinfo.put()
		
		group = Group(shortname=group_shortname, fullname=group_fullname,
					  creator=userinfo)
		group.put()		
		
		relationship = GroupUserInfo(group=group, user=userinfo, 
									 groupname=group.shortname)
		relationship.put()
		
		if userinfo.lastposted == None:
			self.redirect("/profile");
			return
		
		self.redirect("/" + group.shortname)
