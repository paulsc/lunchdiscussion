from ld.utils import LDContextHandler
import cgi
from google.appengine.api.mail import is_email_valid
from uuid import uuid4
from ld.models import InviteCode
from google.appengine.api import mail
import logging

class InviteHandler(LDContextHandler):
	def get(self):
		self.render("invite")
		
	def post(self):
		email_address = cgi.escape(self.request.get('email'))
		if not is_email_valid(email_address):
			self.render("invite", {'notification': 'invalid email address'})
			
		invite = InviteCode(uuid=uuid4().hex, group=self.currentgroup)
		invite_link = "http://www.lunchdiscussiont.com/invite/" + invite.uuid
		
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
		
		self.response.out.write('done')
		
class InviteLinkHandler(LDContextHandler):
	def get(self):
		uuid = self.request.path[8:]
		invite = InviteCode.gql("WHERE uuid=:1", uuid).get()
		if invite == None:
			logging.error("invite not found: " + uuid)
			self.error(500)
			
		# TODO
		
		