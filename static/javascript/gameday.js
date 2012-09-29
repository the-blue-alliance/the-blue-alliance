/* This code is based on MadStream, an FRC webcast portal
 * built in collaboration by FRC Teams 604 and 1323.
 */

// For keeping track of view order
var order = new Array();
// views contain webcasts that are supported by the chosen layout
var views = new Array();
// hiddenviews are the contents views that are not supported by the chosen layout
var hiddenviews = new Array();

$(function() {
  createViews();
  layout_2();

  $(window).resize(function(){
	fixLayout();
  });
});


//Return proper player for a given video
function returnFormat($item, viewNum) {
	var temp, overlay;
	if ($item.hasClass('justin')) {
		temp = "<object type='application/x-shockwave-flash' height='100%' width='100%' id='live_embed_player_flash' data='http://www.justin.tv/widgets/live_embed_player.swf?channel=" + $item.attr("id") + "' bgcolor='#000000'><param name='allowFullScreen' value='true' /><param name='allowScriptAccess' value='always' /><param name='allowNetworking' value='all' /><param name='movie' value='http://www.justin.tv/widgets/live_embed_player.swf' /><param name='flashvars' value='hostname=www.justin.tv&channel=" + $item.attr("id") + "&auto_play=true&start_volume=25&enable_javascript=true' /><param name='wmode' value='transparent' /></object>";
	} else if ($item.hasClass('ustream')) {
		temp = "<object id='utv_o_322919' height='100%' width='100%' classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'><param value='http://www.ustream.tv/flash/live/" + $item.attr("id") + "' name='movie' /><param value='true' name='allowFullScreen' /><param value='always' name='allowScriptAccess' /><param value='transparent' name='wmode' /><param value='viewcount=true&autoplay=true&brand=embed&' name='flashvars' /><embed name='utv_e_218829' id='utv_e_209572' flashvars='viewcount=true&autoplay=true&brand=embed&' height='100%' width='100%' allowfullscreen='true' allowscriptaccess='always' wmode='transparent' src='http://www.ustream.tv/flash/live/" + $item.attr("id") + "' type='application/x-shockwave-flash' /></object>";
	} else if ($item.hasClass('livestream')) {
		temp = "<object width='100%' height='100%' id='lsplayer' classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'><param name='movie' value='http://cdn.livestream.com/grid/LSPlayer.swf?channel=" + $item.attr("id") + "&amp;color=0xe7e7e7&amp;autoPlay=true&amp;mute=false&amp;iconColorOver=0x888888&amp;iconColor=0x777777'></param><param name='allowScriptAccess' value='always'></param><param name='allowFullScreen' value='true'></param><param value='transparent' name='wmode' /><embed name='lsplayer' wmode='transparent' src='http://cdn.livestream.com/grid/LSPlayer.swf?channel=" + $item.attr("id") + "&amp;color=0xe7e7e7&amp;autoPlay=true&amp;mute=false&amp;iconColorOver=0x888888&amp;iconColor=0x777777' width='100%' height='100%' allowScriptAccess='always' allowFullScreen='true' type='application/x-shockwave-flash'></embed></object>";
	} else if ($item.hasClass('wmv')) {
		temp = "<iframe width='100%' height='100%' src='/wmv/" + $item.attr("id") + ".php' scrolling='no' style='border:none; margin:0; padding:0; wmode='transparent''></iframe>";
	} else if ($item.hasClass('wmv2')) {
		temp = "<object id='mediaplayer' classid='clsid:22d6f312-b0f6-11d0-94ab-0080c74c7e95' codebase='http://activex.microsoft.com/activex/controls/mplayer/en/nsmp2inf.cab#version=5,1,52,701' standby='loading microsoft windows media player components...' type='application/x-oleobject' width='100%' height='100%'><param name='filename' value='" + $item.attr("id") + "'><param name='animationatstart' value='true'><param name='transparentatstart' value='true'><param name='autostart' value='true'><param name='showcontrols' value='true'><param name='ShowStatusBar' value='true'><param name='windowlessvideo' value='true'><embed src='" + $item.attr("id") + "' autostart='true' showcontrols='true' showstatusbar='1' bgcolor='black' width='100%' height='100%'></object>";
	} else if ($item.hasClass('other_vids')) {
		temp = "<iframe width='100%' height='100%' src='/other_vids/" + $item.attr("id") + ".php' scrolling='no' style='border:none; margin:0; padding:0; wmode='transparent''></iframe>";
	}
	temp = 'hello'
	temp = "<iframe width='100%' height='100%' src='http://www.chiefdelphi.com' scrolling='no' style='border:none; margin:0; padding:0; wmode='transparent''></iframe>";
	overlay = "<div id='overlay_" + viewNum + "' class='overlay' alt='" + $item.attr("alt") + "'>" +
		"<div class='overlay-title'>" + $item.attr("alt") + "</div>" +
		"<div id='close_" + viewNum + "' class='view-close'>" +
		"<i class='icon-remove icon-white' rel='tooltip' data-placement='left' title='Close'></i></div>" +
		"<div id='swap_" + viewNum + "' class='swap'>" +
		"<i class='icon-move icon-white' rel='tooltip' data-placement='left' title='Drag to another screen to swap'></i></div></div>";
	// Combines the proper video player with overlay
	return temp + overlay;
}

//Create Views
var default_view = "<div class='empty_info'>Drag and drop an event from the 'Webcasts' menu to assign it to this screen.</div><div class='div_helper'></div>";

function createViews(){
  var maxViews = 6;
  for (var n = 0; n < maxViews; n++) {
    var view="<div id='view_" + n + "' class='view'>" + default_view + "</div>";
    $(view).appendTo('.video_container');
    views[n] = view;
    hiddenviews[n] = default_view;
    order[n] = n;
  }
}

// Setup Draggable/Droppable
function setupDragDrop() {
	var swapping = false;
				
	// Let the video items be draggable
	$( ".video_buttons" ).draggable({
		drag: function() {$('.webcasts').addClass('webcasts-show');},
		stop: function() {$('.webcasts').removeClass('webcasts-show');},
		revert: "invalid",
		helper: "clone",
		cursor: "move",
		containment: ".webcasts_panel",
	});
	
	// Let the views be droppable, accepting the video items OR drag handles
	$('.view').droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $(this));
			} else {
				var view_num = parseInt(/view_(\d+)/.exec($(this).attr('id'))[1]);
				setupView(view_num, ui.draggable);
			}
		}
	});

	function setupView(view_num, $item) {
		hiddenviews[view_num] = returnFormat($item, view_num);
		document.getElementById('view_' + view_num).innerHTML = hiddenviews[view_num];
		$("[rel=tooltip]").tooltip();
		setupCloseSwap(view_num);
	}
}

//Setup Close and Swap
function setupCloseSwap(viewNum) {
	// Setup Close
	$("#close_"+viewNum).click(function() {
		document.getElementById("view_"+viewNum).innerHTML = default_view;
		hiddenviews[parseInt(viewNum)] = default_view;
	});
	
	// Setup Swap
	swapping = false;
	$(function() {
		$("#swap_" + viewNum).draggable({
			start: function() {swapping = true;},
			revert: "invalid",
			cursor: "move",
			containment: "#drag_contain",
			stop: function() {/*$("#overlay_"+viewNum).fadeOut(50); */swapping = false; },
			cursorAt: { top: 10, left: 20 },
			helper: function(event) {
				return $("<div class='ui-widget-header'>" + $("#overlay_"+viewNum).attr("alt") + "</div>");
			}
		});
	});
	
	$("#view_" + viewNum).mouseover(function() {
		$("#overlay_"+viewNum).fadeIn(0);
	});
	$("#view_" + viewNum).mouseleave(function() {
		if (!swapping) {
			$("#overlay_"+viewNum).fadeOut(0);
		}
	});
}

//Handle video swap
function swap(dragged, target) {
	var draggedNum = parseInt(/swap_(\d+)/.exec(dragged.attr('id'))[1]);
	var targetNum = parseInt(/view_(\d+)/.exec(target.attr('id'))[1]);

	var draggedIndex = order.indexOf(draggedNum),
		targetIndex = order.indexOf(targetNum);
	
	var temp = order[draggedIndex];
	order[draggedIndex] = order[targetIndex];
	order[targetIndex] = temp;
	
	fixLayout();
}

//Layout Changing Control
var height, width, current_layout, last_layout, num_views;
// num_views[layout_number] = number of views provided by that layout
num_views = [1, 2, 3, 4, 5, 6, 4]

// Fixes layout. Call this if window resized, etc.
function fixLayout() {
	eval('layout_' + current_layout + '()');
}

// Adds or removes proper views, sets up close/swap
function addRemoveViews(current_layout, last_layout) {
	// Add views that weren't visible in last layout
	for (var i = num_views[last_layout]; i < num_views[current_layout]; i++) {
		$(views[parseInt(order[i])]).appendTo('.video_container');
		document.getElementById('view_'+order[i]).innerHTML = hiddenviews[parseInt(order[i])];
	}
	
	// Remove views that are't visible in current layout
	for (var i = num_views[current_layout]; i < order.length; i++) {
		$("#view_"+order[i]).remove();
	}
	
	for (var i = 0; i < num_views[current_layout]; i++) {
		setupCloseSwap(order[i]);
	}
	
	setupDragDrop();
}

// Defines the layouts
function layout_0() {
	current_layout = 0;
	addRemoveViews(current_layout, last_layout);
	
	height = $(".video_container").height();
	width = $(".video_container").width();

	$("#view_"+order[0]).width(width);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	last_layout = current_layout;
}

function layout_1() {
	current_layout = 1;
	addRemoveViews(current_layout, last_layout);
		
	height = $(".video_container").height();
	width = $(".video_container").width();

	$("#view_"+order[0]).width(width*0.5);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	
	$("#view_"+order[1]).width(width*0.5);
	$("#view_"+order[1]).height(height);
	$("#view_"+order[1]).css('top', 0);
	$("#view_"+order[1]).css('left', width*0.5);
	last_layout = current_layout;
}

function layout_2() {
	current_layout = 2;
	addRemoveViews(current_layout, last_layout);

	height = $(".video_container").height();
	width = $(".video_container").width();
	
	$("#view_"+order[0]).width(width*0.65);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	
	$("#view_"+order[1]).width(width*0.35);
	$("#view_"+order[1]).height(height*0.5);
	$("#view_"+order[1]).css('top', 0);
	$("#view_"+order[1]).css('left', width*0.65);
	
	$("#view_"+order[2]).width(width*0.35);
	$("#view_"+order[2]).height(height*0.5);
	$("#view_"+order[2]).css('top', height*0.5);
	$("#view_"+order[2]).css('left', width*0.65);
	last_layout = current_layout;
}

function layout_3() {
	current_layout = 3;
	addRemoveViews(current_layout, last_layout);
		
	height = $(".video_container").height();
	width = $(".video_container").width();

	$("#view_"+order[0]).width(width*0.5);
	$("#view_"+order[0]).height(height*0.5);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	
	$("#view_"+order[1]).width(width*0.5);
	$("#view_"+order[1]).height(height*0.5);
	$("#view_"+order[1]).css('top', 0);
	$("#view_"+order[1]).css('left', width*0.5);
	
	$("#view_"+order[2]).width(width*0.5);
	$("#view_"+order[2]).height(height*0.5);
	$("#view_"+order[2]).css('top', height*0.5);
	$("#view_"+order[2]).css('left', 0);
	
	$("#view_"+order[3]).width(width*0.5);
	$("#view_"+order[3]).height(height*0.5);
	$("#view_"+order[3]).css('top', height*0.5);
	$("#view_"+order[3]).css('left', width*0.5);
	last_layout = current_layout;
}

function layout_4() {
	current_layout = 4;
	addRemoveViews(current_layout, last_layout);
		
	height = $(".video_container").height();
	width = $(".video_container").width();

	$("#view_"+order[0]).width(width*0.75);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	
	$("#view_"+order[1]).width(width*0.25);
	$("#view_"+order[1]).height(height*0.25);
	$("#view_"+order[1]).css('top', 0);
	$("#view_"+order[1]).css('left', width*0.75);
	
	$("#view_"+order[2]).width(width*0.25);
	$("#view_"+order[2]).height(height*0.25);
	$("#view_"+order[2]).css('top', height*0.25);
	$("#view_"+order[2]).css('left', width*0.75);
	
	$("#view_"+order[3]).width(width*0.25);
	$("#view_"+order[3]).height(height*0.25);
	$("#view_"+order[3]).css('top', height*0.5);
	$("#view_"+order[3]).css('left', width*0.75);

	$("#view_"+order[4]).width(width*0.25);
	$("#view_"+order[4]).height(height*0.25);
	$("#view_"+order[4]).css('top', height*0.75);
	$("#view_"+order[4]).css('left', width*0.75);
	last_layout = current_layout;
}

function layout_5() {
	current_layout = 5;
	addRemoveViews(current_layout, last_layout);
		
	height = $(".video_container").height();
	width = $(".video_container").width();
	

	$("#view_"+order[0]).width(width*0.34);
	$("#view_"+order[0]).height(height*0.5);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	
	$("#view_"+order[1]).width(width*0.33);
	$("#view_"+order[1]).height(height*0.5);
	$("#view_"+order[1]).css('top', 0);
	$("#view_"+order[1]).css('left', width*0.34);
	
	$("#view_"+order[2]).width(width*0.33);
	$("#view_"+order[2]).height(height*0.5);
	$("#view_"+order[2]).css('top', 0);
	$("#view_"+order[2]).css('left', width*0.67);
	
	$("#view_"+order[3]).width(width*0.34);
	$("#view_"+order[3]).height(height*0.5);
	$("#view_"+order[3]).css('top', height*0.5);
	$("#view_"+order[3]).css('left', 0);

	$("#view_"+order[4]).width(width*0.33);
	$("#view_"+order[4]).height(height*0.5);
	$("#view_"+order[4]).css('top', height*0.5);
	$("#view_"+order[4]).css('left', width*0.34);

	$("#view_"+order[5]).width(width*0.33);
	$("#view_"+order[5]).height(height*0.5);
	$("#view_"+order[5]).css('top', height*0.5);
	$("#view_"+order[5]).css('left', width*0.67);
	last_layout = current_layout;
}

function layout_6() {
	current_layout = 6;
	addRemoveViews(current_layout, last_layout);

	height = $(".video_container").height();
	width = $(".video_container").width();

	$("#view_"+order[0]).width(width*0.75);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).css('top', 0);
	$("#view_"+order[0]).css('left', 0);
	
	$("#view_"+order[1]).width(width*0.25);
	$("#view_"+order[1]).height(height*0.34);
	$("#view_"+order[1]).css('top', 0);
	$("#view_"+order[1]).css('left', width*0.75);
	
	$("#view_"+order[2]).width(width*0.25);
	$("#view_"+order[2]).height(height*0.33);
	$("#view_"+order[2]).css('top', height*0.34);
	$("#view_"+order[2]).css('left', width*0.75);
	
	$("#view_"+order[3]).width(width*0.25);
	$("#view_"+order[3]).height(height*0.33);
	$("#view_"+order[3]).css('top', height*0.67);
	$("#view_"+order[3]).css('left', width*0.75);
	last_layout = current_layout;
}
