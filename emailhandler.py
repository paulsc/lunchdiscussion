import logging, email
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app

from models import ReplyTo, UserInfo

def send_notification(message, suggestion):
	currentuser = users.get_current_user()
	def f(i): 
		return i.nickname != "" and i.user != currentuser and i.email != 'none'
	targets = filter(f, UserInfo.get_active_crew())

	def send_to_target(target):
		email = mail.EmailMessage(sender="discuss@lunchdiscussion.com")
		email.subject = "Lunchdiscussion.com update"
		email.body = "lunchdiscussion.com update\n " + message
		email.to = "%s <%s>" % (target.nickname, target.email)
		email.to = "paul <paul167@gmail.com"
		reply_to = ReplyTo(user=target, suggestion=suggestion)
		email.reply_to = str(reply_to)
		email.send()
		reply_to.put()
	
	map(send_to_target, targets)
	
def notify_new_comment(comment, suggestion):
	body = "On '%s'\n%s: %s" % (suggestion.restaurant.name, 
								UserInfo.current().nickname, comment)
	send_notification(body, suggestion)

def notify_new_suggestion(suggestion):
	body = "%s suggests going to '%s' for lunch." % \
			(UserInfo.current().nickname, suggestion.restaurant.name)
	send_notification(body, suggestion)		
	

class IncomingMailHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("Received a message from: " + mail_message.sender)

def main():
	application = webapp.WSGIApplication([IncomingMailHandler.mapping()], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()