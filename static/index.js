
function buildGroupURL(subsection) {
	path = window.location.pathname;
	if (path.endsWith('/')) {
		return path + subsection;
	}
	else {
		return path + '/' + subsection;
	}
}
	
function addRestaurant() {
	new Ajax.Updater('restaurants', buildGroupURL('restaurants'),
			{ method: 'post', 
			  parameters: { name: $F('restaurant_name') } });
	$('restaurant_name').value = '';
}

function showLoadingSuggestions() {
	$('suggestions').innerHTML = 
		"<div class='loading_suggestions'>" + $('suggestions').innerHTML + "</div>";
}

function newSuggestion(restaurantKey) {
	showLoadingSuggestions();
	new Ajax.Updater('suggestions', buildGroupURL('suggestions'),
			{ method: 'post', 
			  parameters: { action: 'add_suggestion', restaurant: restaurantKey } });
}

function newComment(sug, text) {
	showLoadingSuggestions();
	new Ajax.Updater('suggestions', buildGroupURL('suggestions'),
			{ method: 'post', 
			  parameters: { action: 'add_comment', suggestion: sug, text: text } });
}

function removeSuggestion(key) {
	var answer = confirm("Are you sure?");
	if (answer) {
		showLoadingSuggestions();
		new Ajax.Updater('suggestions', buildGroupURL('suggestions'),
				{ method: 'post', 
				  parameters: { action: 'remove_suggestion', suggestion: key } });
	}
}

function removeComment(key) {
	var answer = confirm("Are you sure?");
	if (answer) {
		showLoadingSuggestions();
		new Ajax.Updater('suggestions', buildGroupURL('suggestions'),
				{ method: 'post', 
				  parameters: { action: 'remove_comment', comment: key } });
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
