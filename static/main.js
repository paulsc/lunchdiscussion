new Ajax.Updater('restaurants', '/restaurants', { method: 'get' });
new Ajax.Updater('suggestions', '/suggestions', { method: 'get' });
new Ajax.Updater('twitter', '/twitter', { method: 'get' });

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

function removeComment(key) {
	var answer = confirm("Are you sure?");
	if (answer) {
		new Ajax.Updater('suggestions', 
				'/suggestions?remove_comment=' + key,
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

function showRestaurantPopup(restaurant) {
	myLightWindow.activateWindow({
			href: '/restaurant-info?restaurant=' + restaurant, 
			height: 400,
			width: 500,
	});
}

function $RF(el, radioGroup) {
	if($(el).type && $(el).type.toLowerCase() == 'radio') {
		var radioGroup = $(el).name;
		var el = $(el).form;
	} else if ($(el).tagName.toLowerCase() != 'form') {
		return false;
	}

	var checked = $(el).getInputs('radio', radioGroup).find(
		function(re) {return re.checked;}
	);
	return (checked) ? $F(checked) : null;
}		
			


