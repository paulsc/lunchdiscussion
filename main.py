import wsgiref.handlers
from google.appengine.ext import webapp

from ld.views import IndexHandler, ProfileHandler, RestaurantHandler,\
	RestaurantInfoHandler, SuggestionHandler, AvatarHandler, RatingHandler,\
	StatsHandler, HomeHandler
from ld.emailhandler import EmailTaskHandler, IncomingMailHandler
from ld.cron import DailyCronHandler
from ld.signup import SignupHandler
from ld.models import GROUP_SHORTNAME_REGEXP

def main():
	application = webapp.WSGIApplication([('/', IndexHandler),
										  ('/signup', SignupHandler),
										  ('/profile', ProfileHandler),
										  ('/restaurant-info', RestaurantInfoHandler),
										  ('/restaurants', RestaurantHandler),
										  ('/suggestions', SuggestionHandler),
										  ('/avatar', AvatarHandler),
										  ('/rate', RatingHandler),
										  ('/stats', StatsHandler),
										  ("/emailtask", EmailTaskHandler),
										  IncomingMailHandler.mapping(),
										  ('/cron/daily', DailyCronHandler),
										  ('/%s/?' % GROUP_SHORTNAME_REGEXP, HomeHandler)
										  ],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)
		
if __name__ == "__main__":
	main()