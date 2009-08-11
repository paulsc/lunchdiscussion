from google.appengine.api import users
from google.appengine.api import mail

from datetime import datetime
from datetime import date
from datetime import timedelta
from tzinfo import Eastern

from models import UserInfo
from models import Suggestion

def is_morning():
	now = datetime.now(Eastern)
	return now.hour < 14

def user_info():
	return UserInfo.gql("WHERE user = :1", users.get_current_user()).get()
	
def ask_to_rate():
	today = date.today()
	yesterday = today - timedelta(1)
	userinfo = user_info()
	if is_morning():
		return not userinfo.voted_for_day(yesterday) and get_suggestions(yesterday).count() > 0
	else:
		return not userinfo.voted_for_day(today) and get_suggestions(today).count() > 0
		
def get_suggestions(date):
	return Suggestion.gql("WHERE date=DATE(:1, :2, :3)", date.year, date.month, date.day)

def send_notification(message):
	infos = UserInfo.get_active_crew()
	targets = []
	for info in infos:
		if info.nickname != "" and info.user != users.get_current_user() and user_info().email != 'none':
			targets.append(info)
	if len(targets) == 0:
		return
	to = ",".join([ x.nickname + " <" + x.email + ">" for x in targets ])
	message = "www.lunchdiscussion.com update\n " + message
	mail.send_mail(sender="discuss@lunchdiscussion.com", to=to, subject="Lunch discussion update", body=message)

def notify_new_message(comment, suggestion):
	body = "On '" + suggestion.restaurant.name + "'\n"  + user_info().nickname + ": " + comment
	send_notification(body)

def notify_new_suggestion(suggestion):
	body = user_info().nickname + " suggests going to '" + suggestion.restaurant.name + "' for lunch."
	send_notification(body)		

		