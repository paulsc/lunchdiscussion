import wsgiref.handlers
from google.appengine.ext import webapp

from ld.views import MainHandler, ProfileHandler, RestaurantHandler,\
	RestaurantInfoHandler, SuggestionHandler, AvatarHandler, RatingHandler,\
	StatsHandler
from ld.emailhandler import EmailTaskHandler, IncomingMailHandler
from ld.cron import DailyCronHandler
from ld.signup import SignupHandler

def main():
	application = webapp.WSGIApplication([('/', MainHandler),
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
										  ],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)
		
if __name__ == "__main__":
	main()