var GAMES, GAME_DATA, MODE='LEARN';
var CURRENT_ITEM = null, LEARN_HISTORY={}, PLAY_HISTORY = new Set();
var CURRENT_AUDIO = null;

function renderGrid() {
	var table = '';
	var rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
	for (var i=0; i<8; i++){
		var tr = '<tr>';
		for (var j=1; j<=8; j++){
			tr += '<td id="' + rows[i] + j + '" onclick="keyPressed(this.id)"></td>';
		}
		tr += '</tr>';
		table += tr;
	}
	$('.grid').html(table);

	var data = $.map(GAMES, function (obj) {
	  obj.id = obj.code;
	  obj.text = obj.title
	  return obj;
	});
	console.log(data);

	$('#options').select2({
		data: data,
		placeholder: 'Select game'
	});

	$('#options').on('select2:select', function (e) {
		var data = e.params.data;
		selectGame(data);
	});
	$('#log').text(data);

	$('#mode').change(function() {
  MODE = $(this).prop('checked') ? 'PLAY' : 'LEARN';	    	  
  modeChanged();
  })
}

function modeChanged(){
console.log('Mode: ' + MODE);
if (MODE == 'LEARN'){
	console.log('Select item');
	play_sound('../assets/learn.wav', true);
}
else {
	play_sound('../assets/play.wav', true);
	play();
}
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function play_sound(fname, wait) {
	console.log('Playing ' + fname);

	if (!CURRENT_AUDIO){
		CURRENT_AUDIO = new Audio(fname);
		CURRENT_AUDIO.play();															
	}
	else if (!wait){
		CURRENT_AUDIO.pause();
		CURRENT_AUDIO = new Audio(fname);
		CURRENT_AUDIO.play();										
	}
	else {
		var timer = setInterval(function(){
			if (!(CURRENT_AUDIO.ended || CURRENT_AUDIO.paused))
				return;
			clearInterval(timer);

			CURRENT_AUDIO = new Audio(fname);
			CURRENT_AUDIO.play();															
		}, 500)				
	}					
}

function success(){
	play_sound('../assets/success.wav');
}

function failure(){
	play_sound('../assets/failure.wav');
}

function play(){
	var new_items = [];
	$.each(GAME_DATA.play, function(key, val){
		if (!PLAY_HISTORY.has(key)){
			new_items.push(key);
		}
	})
	if (new_items.length == 0){
		new_items = Object.keys(GAME_DATA.play);
		PLAY_HISTORY.clear();						
	}
	var randindx = Math.floor(Math.random() * new_items.length);
	var item = new_items[randindx];
	PLAY_HISTORY.add(item);
	CURRENT_ITEM = item;

	play_sound(getPath(item), true);
}

function learn(selection){
	console.log(selection);
	var new_items = [];
	var items = GAME_DATA.items[selection].learn;
	$.each(items, function(idx, data){
		if (!LEARN_HISTORY[selection].has(data)){
			new_items.push(data);							
		}
	})
	if (new_items.length == 0) {
		new_items = items;
		LEARN_HISTORY[selection].clear();
	}
	var randindx = Math.floor(Math.random() * new_items.length);
	var item = new_items[randindx];
	LEARN_HISTORY[selection].add(item)
	play_sound(getPath(item));		
}

function getPath(item){
	return '../outputs/' + GAME_DATA.code + '/' + item;
}

function selectGame(game){
	$('#title').text(game.title);
	$.get('../outputs/' + game.code + '/config.yaml', function(data){
		GAME_DATA = jsyaml.load(data);
		$('#title').text(GAME_DATA.title_text || 'Unknown');
		$('.grid').css('background-image', 'url(' + getPath('game.jpg') + ')')
		
		LEARN_HISTORY = {}; PLAY_HISTORY.clear();
		GAME_DATA.play = {};
		$.each(GAME_DATA.items, function(idx, item){
			LEARN_HISTORY[idx] = new Set();
			$.each(item.play, function(pidx, play_item){
				GAME_DATA.play[play_item] = idx;
			})
		})			

		modeChanged();
	})
}

function keyPressed(id){
	if (!GAME_DATA)
		return;

	if (GAME_DATA.layout[id] == undefined)
		return;

	var new_items = [];
	var selection = GAME_DATA.layout[id] - 1;
	if (MODE == 'LEARN'){
		learn(selection);
	}
	else {
		if (selection == GAME_DATA.play[CURRENT_ITEM]) {
			success();
		}
		else {
			failure();
		}
		play();
	}
}

