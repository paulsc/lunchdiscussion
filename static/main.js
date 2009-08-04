new Ajax.Updater('restaurants', '/restaurants', 
		{ method: 'get' });

new Ajax.Updater('suggestions', '/suggestions',
		{ method: 'get' });

function addRestaurant() {
	new Ajax.Updater('restaurants', 
			'/restaurants?add=' + $F('restaurant_name'),
			{ method: 'get' });
	$('restaurant_name').value = '';
}

function newSuggestion(restaurantKey) {
	new Ajax.Updater('suggestions', 
			'/suggestions?add=' + restaurantKey,
			{ method: 'get' });
}

function newComment(sug, text) {
	new Ajax.Updater('suggestions', '/suggestions', { 
				method: 'post', 
				parameters: { suggestion: sug, text: text }
			});
}

function removeSuggestion(key) {
	var answer = confirm("Are you sure?");
	if (answer) {
		new Ajax.Updater('suggestions', 
				'/suggestions?remove=' + key,
				{ method: 'get' });
	}
}

function addRating(restaurantKey, rating) {
	new Ajax.Request('/rate?restaurant=' + restaurantKey + '&rating=' + rating, { 
			method: 'get',
		  	onSuccess: function(transport) {
		  		alert('okay thanks');
		  	}
		 });
}

function showRatingPopup() {
	myLightWindow.activateWindow({
			href: 'rate', 
			title: 'Hey, how was lunch ?', 
			height: 400,
			width: 600,
	});
}

function showProfilePopup(user) {
	myLightWindow.activateWindow({
			href: '/profile?user=' + user, 
			height: 300,
			width: 300,
	});
}


