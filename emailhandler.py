import uuid
import logging
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail

from models import ReplyTo, UserInfo
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
					break	
			return len(lines)

		empty_line = find_empty_line(lines)
		logging.info(empty_line)
		comment = "\n".join(lines[:empty_line])
		post_comment(comment, reply_to.user, reply_to.suggestion)
		logging.info("Email comment posted from: " + reply_to.user.nickname)


class EmailTaskHandler(webapp.RequestHandler):
	def post(self):
		suggestion = db.get(self.request.get("suggestion"))
		target = db.get(self.request.get("target"))
		message = self.request.get("message")

		logging.info("email task: %s %s %s" % (str(suggestion), str(target), message))
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "Lunchdiscussion.com update"
		email.body = "www.lunchdiscussion.com update\n" + message
		email.to = "%s <%s>" % (target.nickname, target.email)
		reply_to = ReplyTo(user=target, suggestion=suggestion, uuid=uuid.uuid4().hex)
		email.reply_to = str(reply_to)
		email.send()
		reply_to.put()
	

def main():
	application = webapp.WSGIApplication([
			IncomingMailHandler.mapping(),
			("/emailtask", EmailTaskHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
