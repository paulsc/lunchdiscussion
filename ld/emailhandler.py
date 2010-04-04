import uuid
import logging

from google.appengine.ext import db
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.api import mail

from models import ReplyTo
from utils import post_comment

class IncomingMailHandler(InboundMailHandler):
	def receive(self, mail):
		uuid = mail.to[:mail.to.index('@')]
		reply_to = ReplyTo.gql('WHERE uuid = :1', uuid).get()

		if reply_to == None:
			logging.error("Inbound email: cound'nt find ReplyTo for " + uuid)
			return

		bodies = mail.bodies('text/plain')
		body = bodies.next()[1].decode()
		lines = body.splitlines()

		def find_empty_line(lines):
			for i in range(len(lines)):
				if lines[i] == "":
					return i			
			return len(lines)

		empty_line = find_empty_line(lines)
		comment = "\n".join(lines[:empty_line])
		post_comment(comment, reply_to.user, reply_to.suggestion)
		logging.info("Email comment posted from: " + reply_to.user.nickname)


class EmailTaskHandler(webapp.RequestHandler):
	def post(self):
		suggestion = db.get(self.request.get('suggestion'))
		targets = self.request.get('targets').split(',')
		message = self.request.get('message')
		reply_to = (self.request.get('reply_to') == 'true')
		
		targets = [ db.get(key) for key in targets ]

		emails = [ user.email for user in targets ]
		emails = ",".join(emails)

		grouplink = 'www.lunchdiscussion.com/' + suggestion.group.shortname

		logging.info("email task to: %s \"%s\"" % (emails, message))
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "Lunchdiscussion.com update"
		email.body = '%s update\n%s' % (grouplink, message)
		
		if reply_to:
			for target in targets:
				email.to = "%s <%s>" % (target.nickname, target.email)
				#email.to = "paul <paul167@gmail.com>"
				reply_to = ReplyTo(user=target, suggestion=suggestion, uuid=uuid.uuid4().hex)
				email.reply_to = str(reply_to)
				reply_to.put()
				email.send()
		else:
			emails = [ "%s <%s>" % (target.nickname, target.email) for target in targets ]
			email.to = ', '.join(emails)
			email.send()

