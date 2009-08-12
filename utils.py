from google.appengine.api import mail
from google.appengine.api import users

from datetime import datetime
from datetime import date
from datetime import timedelta
from tzinfo import Eastern

from models import UserInfo
from models import Suggestion

def incr(var, val = 1): return 1 if var == None else var + val

def is_morning():
	now = datetime.now(Eastern)
	return now.hour < 14
	
def ask_to_rate():
	today = date.today()
	yesterday = today - timedelta(1)
	userinfo = UserInfo.current()
	if is_morning():
		return (not userinfo.voted_for_day(yesterday) 
				and Suggestion.get_for_day(yesterday).count() > 0)
	else:
		return (not userinfo.voted_for_day(today) 
				and Suggestion.get_for_day(today).count() > 0)
		
def send_notification(message):
	currentuser = users.get_current_user()
	def f(i): i.nickname != "" and i.user != currentuser and i.email != 'none'
	targets = filter(f, UserInfo.get_active_crew())
	if len(targets) == 0:
		return
	to = ",".join([ x.nickname + " <" + x.email + ">" for x in targets ])
	message = "www.lunchdiscussion.com update\n " + message
	mail.send_mail(sender="discuss@lunchdiscussion.com", to=to, 
					subject="Lunch discussion update", body=message)

def notify_new_message(comment, suggestion):
	body = "On '%s'\n%s: %s" % (suggestion.restaurant.name, 
								UserInfo.current().nickname, comment)
	send_notification(body)

def notify_new_suggestion(suggestion):
	body = "%s suggests going to '%s' for lunch." % \
			(UserInfo.current().nickname, suggestion.restaurant.name)
	send_notification(body)		
