from ld.utils import LDContextHandler, is_empty
import cgi
from google.appengine.api.mail import is_email_valid
from uuid import uuid4
from ld.models import InviteCode, UserInfo, GroupUserInfo
from google.appengine.api import mail, users
import logging

class InviteHandler(LDContextHandler):
	def get(self):
		self.render("invite")
		
	def post(self):
		email_address = cgi.escape(self.request.get('email'))
		if not is_email_valid(email_address):
			self.render("invite", {'notification': 'invalid email address'})
			
		invite = InviteCode(uuid=uuid4().hex, group=self.currentgroup)
		invite_link = "http://www.lunchdiscussion.com/invite/" + invite.uuid
		
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "%s invited you to Lunchdiscussion.com" % self.currentuser.nickname
		email.body = """%s invited you to join the "%s" group on Lunchdiscussion.com

click <a href="%s">here</a> to join the group.""" % (self.currentuser.nickname, 
													 self.currentgroup.fullname, 
													 invite_link)
		email.to = email_address
		#email.to = "paul <paul167@gmail.com>"
		email.send()
		invite.put()
		
		logging.info(invite_link)
		self.render('invite', notification='invite sent to %s!' % email_address)
		
class InviteLinkHandler(LDContextHandler):
	def get(self, uuid):
		invite = InviteCode.gql("WHERE uuid=:1", uuid).get()
		if invite == None:
			logging.error("invite not found: " + uuid)
			self.error(500)
			return

		if self.currentuser == None:
			self.currentuser = UserInfo(user=users.get_current_user())
			self.currentuser.put()
			
		relationship = GroupUserInfo.gql("WHERE user=:1 AND group=:2", self.currentuser, invite.group).get()
		if relationship == None:
			relationship = GroupUserInfo(user=self.currentuser, group=invite.group, 
										 groupname=invite.group.shortname)
			relationship.put()
			
		invite.delete()
			
		if is_empty(self.currentuser.nickname):
			self.render('edit_profile')
			return
		
		self.redirect('/')
			
			
		