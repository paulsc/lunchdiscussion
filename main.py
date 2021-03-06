import wsgiref.handlers
from google.appengine.ext import webapp

from ld.views import IndexHandler, ProfileHandler, RestaurantHandler,\
	RestaurantInfoHandler, SuggestionHandler, AvatarHandler, RatingHandler,\
	StatsHandler, HomeHandler, AdminHandler
from ld.emailhandler import EmailTaskHandler, IncomingMailHandler
from ld.cron import DailyCronHandler
from ld.signup import SignupHandler
from ld.models import RE_GROUPNAME
from ld.invite import InviteHandler, InviteLinkHandler

def main():
	application = webapp.WSGIApplication([('/', IndexHandler),
										  ('/signup', SignupHandler),
										  ('/profile', ProfileHandler),
										  ('/avatar', AvatarHandler),
										  ("/task/email", EmailTaskHandler),
										  IncomingMailHandler.mapping(),
										  ('/cron/daily', DailyCronHandler),
										  ('/%s/stats' % RE_GROUPNAME, StatsHandler),
										  ('/%s/restaurant-info' % RE_GROUPNAME, RestaurantInfoHandler),
										  ('/%s/restaurants' % RE_GROUPNAME, RestaurantHandler),
										  ('/%s/suggestions' % RE_GROUPNAME, SuggestionHandler),
										  ('/%s/rate' % RE_GROUPNAME, RatingHandler),
										  ('/%s/invite' % RE_GROUPNAME, InviteHandler),
										  ('/%s/admin' % RE_GROUPNAME, AdminHandler),
										  ('/invite/(\w+)', InviteLinkHandler),
										  ('/%s/?' % RE_GROUPNAME, HomeHandler)
										  ],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)
		
if __name__ == "__main__":
	main()