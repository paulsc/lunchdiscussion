import wsgiref.handlers
from google.appengine.ext import webapp
from ld.views import MainHandler, ProfileHandler, RestaurantHandler,\
	RestaurantInfoHandler, SuggestionHandler, AvatarHandler, RatingHandler,\
	StatsHandler

def main():
	application = webapp.WSGIApplication([('/', MainHandler),
										  ('/profile', ProfileHandler),
										  ('/restaurant-info', RestaurantInfoHandler),
										  ('/restaurants', RestaurantHandler),
										  ('/suggestions', SuggestionHandler),
										  ('/avatar', AvatarHandler),
										  ('/rate', RatingHandler),
										  ('/stats', StatsHandler)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)
		
if __name__ == "__main__":
	main()