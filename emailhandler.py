import uuid
import logging, email
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app

from models import ReplyTo, UserInfo, Comment

# following 3 functions need cleaning up
def send_notification(message, suggestion, exclude_user):
	def f(i): 
		return i.nickname != "" and i.user != exclude_user and i.email != 'none'
	targets = filter(f, UserInfo.get_active_crew())

	def send_to_target(target):
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "Lunchdiscussion.com update"
		email.body = "www.lunchdiscussion.com update\n " + message
		email.to = "%s <%s>" % (target.nickname, target.email)
		reply_to = ReplyTo(user=target, suggestion=suggestion, uuid=uuid.uuid4().hex)
		email.reply_to = str(reply_to)
		email.send()
		reply_to.put()
	
	map(send_to_target, targets)
	
def notify_new_comment(text, comment):
	body = "On '%s'\n%s: %s" % (comment.suggestion.restaurant.name, 
								comment.author.nickname, text)
	send_notification(body, comment.suggestion, comment.author.user)

def notify_new_suggestion(suggestion):
	body = "%s suggests going to '%s' for lunch." % \
			(suggestion.author.nickname, suggestion.restaurant.name)
	send_notification(body, suggestion, suggestion.author.user)		
	

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
			return i

		empty_line = find_empty_line(lines)
		comment = "\n".join(lines[:empty_line])
		Comment.post(comment, reply_to.user, reply_to.suggestion)
		logging.info("Email comment posted from: " + reply_to.user.nickname)


def main():
	application = webapp.WSGIApplication([IncomingMailHandler.mapping()], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
