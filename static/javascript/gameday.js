/* This code is based on MadStream, an FRC webcast portal
 * built in collaboration by FRC Teams 604 and 1323.
 */

$(function() {
// Setup Video Areas
var view_1, view_2, view_3, view_4, view_5, view_6, view_text, tempview_1, tempview_2, tempview_3, tempview_4, tempview_5, tempview_6;
tempview_1=tempview_2=tempview_3=tempview_4=tempview_5=tempview_6=view_text="Drag and drop an event from the 'Webcasts' menu to assign it to this screen. Please press F11 for fullscreen experience.";

view_1="<div id='view_1' style='text-align:center; margin: 0px; background:#222222; outline:black 1px solid; visibility: visible;'>" + view_text + "</div>";
view_2="<div id='view_2' style='text-align:center; margin: 0px; background:#222222; outline:black 1px solid; visibility: visible;'>" + view_text + "</div>";
view_3="<div id='view_3' style='text-align:center; margin: 0px; background:#222222; outline:black 1px solid; visibility: visible;'>" + view_text + "</div>";
view_4="<div id='view_4' style='text-align:center; margin: 0px; background:#222222; outline:black 1px solid; visibility: visible;'>" + view_text + "</div>";
view_5="<div id='view_5' style='text-align:center; margin: 0px; background:#222222; outline:black 1px solid; visibility: visible;'>" + view_text + "</div>";
view_6="<div id='view_6' style='text-align:center; margin: 0px; background:#222222; outline:black 1px solid; visibility: visible;'>" + view_text + "</div>";

$(view_1).appendTo('#video_container');
$(view_2).appendTo('#video_container');
$(view_3).appendTo('#video_container');
$(view_4).appendTo('#video_container');
$(view_5).appendTo('#video_container');
$(view_6).appendTo('#video_container');

// Keep track of video order

var order = new Array();
order[0]="1";
order[1]="2";
order[2]="3";
order[3]="4";
order[4]="5";
order[5]="6";

var views = new Array();
views[0] = view_1;
views[1] = view_2;
views[2] = view_3;
views[3] = view_4;
views[4] = view_5;
views[5] = view_6;

var tempviews = new Array();
tempviews[0] = tempview_1;
tempviews[1] = tempview_2;
tempviews[2] = tempview_3;
tempviews[3] = tempview_4;
tempviews[4] = tempview_5;
tempviews[5] = tempview_6;

// Setup Draggable/Droppable
function setup() {
	var $view_1 = $("#view_1"),
		$view_2 = $("#view_2"),
		$view_3 = $("#view_3"),
		$view_4 = $("#view_4"),
		$view_5 = $("#view_5"),
		$view_6 = $("#view_6"),
		swapping = false;
				
	// Let the video items be draggable
	$( ".video_buttons" ).draggable({
		revert: "invalid",
		helper: "clone",
		cursor: "move",
		containment: "#drag_contain",
		stop: function() {document.getElementById('webcasts_hide').style.display="none"; click = false;}
	});

	// Let the views be droppable, accepting the video items OR drag handles
	$view_1.droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $view_1);
			} else {
				view1( ui.draggable );
			}
		}
	});
	$view_2.droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $view_2);
			} else {
				view2( ui.draggable );
			}
		}
	});
	$view_3.droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $view_3);
			} else {
				view3( ui.draggable );
			}
		}
	});
	$view_4.droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $view_4);
			} else {
				view4( ui.draggable );
			}
		}
	});
	$view_5.droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $view_5);
			} else {
				view5( ui.draggable );
			}
		}
	});
	$view_6.droppable({
		drop: function( event, ui ) {
			if(ui.draggable.hasClass('swap')) {
				swap(ui.draggable, $view_6);
			} else {
				view6( ui.draggable );
			}
		}
	});
}

// Return proper player for a given video
function returnFormat($item, viewNum) {
	var temp;
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
	
	// Combines the proper video player with overlay
	//return temp + "<div id='overlay_"+viewNum+"' alt='"+ $item.attr("alt") +"' style='background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,rgba(0,0,0,1)), color-stop(100%,rgba(0,0,0,0))); z-index:5000; width: 100%; height: 65%; position:absolute; top:0px; left:0px; text-align:right; pointer-events:none;'><h2 style='color:white; float:left; margin:15px;'>" + $item.attr("alt") + "</h2><a id='close_"+viewNum+"' href='#' style='margin:15px; pointer-events:all;'><img src='Images/video_close.png' title='Close' style='margin:10px 0 5px 0;'></img></a><br /><a id='swap_"+viewNum+"' class='swap' href='#' style='margin:15px; pointer-events:all;'><img src='Images/video_swap.png' title='Drag to another screen to swap' style='margin:5px 0 10px 0;'></img></a></div>";
	return temp + "<div id='overlay_"+viewNum+"' alt='"+ $item.attr("alt") +"' style='background: -moz-linear-gradient(top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 40%, rgba(0,0,0,0) 100%);	background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,rgba(0,0,0,1)), color-stop(40%,rgba(0,0,0,0)), color-stop(100%,rgba(0,0,0,0))); background: -webkit-linear-gradient(top, rgba(0,0,0,1) 0%,rgba(0,0,0,0) 40%,rgba(0,0,0,0) 100%); background: -o-linear-gradient(top, rgba(0,0,0,1) 0%,rgba(0,0,0,0) 40%,rgba(0,0,0,0) 100%); background: -ms-linear-gradient(top, rgba(0,0,0,1) 0%,rgba(0,0,0,0) 40%,rgba(0,0,0,0) 100%); background: linear-gradient(top, rgba(0,0,0,1) 0%,rgba(0,0,0,0) 40%,rgba(0,0,0,0) 100%); z-index: 5000; width: 100%; height: 65%; position:absolute; top:0px; left:0px; text-align:right; pointer-events:none;'><h2 style='color:white; float:left; margin:15px;'>" + $item.attr("alt") + "</h2><a id='close_"+viewNum+"' href='#' style='margin:15px; pointer-events:all;'><img src='Images/video_close.png' title='Close' style='margin:10px 0 5px 0; border:none;'></img></a><br /><a id='swap_"+viewNum+"' class='swap' href='#' style='margin:15px; pointer-events:all;'><img src='Images/video_swap.png' title='Drag to another scren to swap' style='margin:5px 0 10px 0; border:none;'></img></a></div>";
}

// Setup Close and Swap
function setupCloseSwap(viewNum) {
	
	// Setup Close
	$("#close_"+viewNum).click(function() {
		document.getElementById("view_"+viewNum).innerHTML = view_text;
		tempviews[parseInt(viewNum)-1] = view_text;
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
				return $("<div class='ui-widget-header' style='width:150px; text-align:center; z-index:100000'>" + $("#overlay_"+viewNum).attr("alt") + "</div>");
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

// Set up the drop events for each view
function view1( $item ) {
	tempviews[0] = returnFormat($item, "1"); 
	document.getElementById('view_1').innerHTML = tempviews[0];
	setupCloseSwap("1");
}
function view2( $item ) {
	tempviews[1] = returnFormat($item, "2"); 
	document.getElementById('view_2').innerHTML = tempviews[1];
	setupCloseSwap("2");
}
function view3( $item ) {
	tempviews[2] = returnFormat($item, "3") 
	document.getElementById('view_3').innerHTML = tempviews[2];
	setupCloseSwap("3");
}
function view4( $item ) {
	tempviews[3] = returnFormat($item, "4") 
	document.getElementById('view_4').innerHTML = tempviews[3];
	setupCloseSwap("4");
}
function view5( $item ) {
	tempviews[4]= returnFormat($item, "5") 
	document.getElementById('view_5').innerHTML = tempviews[4];
	setupCloseSwap("5");
}
function view6( $item ) {
	tempviews[5] = returnFormat($item, "6") 
	document.getElementById('view_6').innerHTML = tempviews[5];
	setupCloseSwap("6");
}

//Layout Control
var height, width, current_view;
function layout_1() {
	current_view = 1;
	
	height = $("#video_container").height();
	width = $("#video_container").width();
	
	$("#view_"+order[1]).remove();
	$("#view_"+order[2]).remove();
	$("#view_"+order[3]).remove();
	$("#view_"+order[4]).remove();
	$("#view_"+order[5]).remove();

	$("#view_"+order[0]).width(width);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).offset({top: 30, left: 0});
}
function layout_2() {
	if (current_view == 1) {
		$(views[parseInt(order[1])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[1]).innerHTML = tempviews[parseInt(order[1])-1];
	}
	setup();
	setupCloseSwap(order[1]);		
	current_view = 2;
		
	height = $("#video_container").height();
	width = $("#video_container").width();
	
	$("#view_"+order[2]).remove();
	$("#view_"+order[3]).remove();
	$("#view_"+order[4]).remove();
	$("#view_"+order[5]).remove();

	$("#view_"+order[0]).width(width*0.5);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).offset({top: 30, left: 0});
	
	$("#view_"+order[1]).width(width*0.5);
	$("#view_"+order[1]).height(height);
	$("#view_"+order[1]).offset({top: 30, left: width*0.5});
}
function layout_3() {
	if (current_view == 1) {
		$(views[parseInt(order[1])-1]).appendTo('#video_container');
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[1]).innerHTML = tempviews[parseInt(order[1])-1];
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
	} else if (current_view == 2) {
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
	}
	
	setup();
	setupCloseSwap(order[1]);
	setupCloseSwap(order[2]);
	current_view = 3;
		
	height = $("#video_container").height();
	width = $("#video_container").width();
	
	$("#view_"+order[3]).remove();
	$("#view_"+order[4]).remove();
	$("#view_"+order[5]).remove();

	$("#view_"+order[0]).width(width*0.65);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).offset({top: 30, left: 0});
	
	$("#view_"+order[1]).width(width*0.35);
	$("#view_"+order[1]).height(height*0.5);
	$("#view_"+order[1]).offset({top: 30, left: width*0.65});
	
	$("#view_"+order[2]).width(width*0.35);
	$("#view_"+order[2]).height(height*0.5);
	$("#view_"+order[2]).offset({top: 30 + height*0.5, left: width*0.65});
}

function layout_4() {
	if (current_view == 1) {
		$(views[parseInt(order[1])-1]).appendTo('#video_container');
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[1]).innerHTML = tempviews[parseInt(order[1])-1];
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
	} else if (current_view == 2) {
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
	} else if (current_view == 3) {
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
	}
	setup();
	setupCloseSwap(order[1]);
	setupCloseSwap(order[2]);
	setupCloseSwap(order[3]);
	current_view = 4;
		
	height = $("#video_container").height();
	width = $("#video_container").width();

	$("#view_"+order[4]).remove();
	$("#view_"+order[5]).remove();

	$("#view_"+order[0]).width(width*0.5);
	$("#view_"+order[0]).height(height*0.5);
	$("#view_"+order[0]).offset({top: 30, left: 0});
	
	$("#view_"+order[1]).width(width*0.5);
	$("#view_"+order[1]).height(height*0.5);
	$("#view_"+order[1]).offset({top: 30, left: width*0.5});
	
	$("#view_"+order[2]).width(width*0.5);
	$("#view_"+order[2]).height(height*0.5);
	$("#view_"+order[2]).offset({top: 30 + height*0.5, left: 0});
	
	$("#view_"+order[3]).width(width*0.5);
	$("#view_"+order[3]).height(height*0.5);
	$("#view_"+order[3]).offset({top: 30 + height*0.5, left: width*0.5});
}
function layout_5() {
	if (current_view == 1) {
		$(views[parseInt(order[1])-1]).appendTo('#video_container');
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[1]).innerHTML = tempviews[parseInt(order[1])-1];
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
	} else if (current_view == 2) {
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
	} else if (current_view == 3) {
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
	} else if ((current_view == 4) || (current_view == 7)) {
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
	}
	setup();
	setupCloseSwap(order[1]);
	setupCloseSwap(order[2]);
	setupCloseSwap(order[3]);
	setupCloseSwap(order[4]);
	current_view = 5;
		
	height = $("#video_container").height();
	width = $("#video_container").width();

	$("#view_"+order[5]).remove();

	$("#view_"+order[0]).width(width*0.75);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).offset({top: 30, left: 0});
	
	$("#view_"+order[1]).width(width*0.25);
	$("#view_"+order[1]).height(height*0.25);
	$("#view_"+order[1]).offset({top: 30, left: width*0.75});
	
	$("#view_"+order[2]).width(width*0.25);
	$("#view_"+order[2]).height(height*0.25);
	$("#view_"+order[2]).offset({top: 30 + height*0.25, left: width*0.75});
	
	$("#view_"+order[3]).width(width*0.25);
	$("#view_"+order[3]).height(height*0.25);
	$("#view_"+order[3]).offset({top: 30 + height*0.5, left: width*0.75});

	$("#view_"+order[4]).width(width*0.25);
	$("#view_"+order[4]).height(height*0.25);
	$("#view_"+order[4]).offset({top: 30 + height*0.75, left: width*0.75});
}
function layout_6() {
	if (current_view == 1) {
		$(views[parseInt(order[1])-1]).appendTo('#video_container');
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		$(views[parseInt(order[5])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[1]).innerHTML = tempviews[parseInt(order[1])-1];
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
		document.getElementById('view_'+order[5]).innerHTML = tempviews[parseInt(order[5])-1];
	} else if (current_view == 2) {
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		$(views[parseInt(order[5])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
		document.getElementById('view_'+order[5]).innerHTML = tempviews[parseInt(order[5])-1];
	} else if (current_view == 3) {
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		$(views[parseInt(order[5])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
		document.getElementById('view_'+order[5]).innerHTML = tempviews[parseInt(order[5])-1];
	} else if ((current_view == 4) || (current_view == 7)) {
		$(views[parseInt(order[4])-1]).appendTo('#video_container');
		$(views[parseInt(order[5])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[4]).innerHTML = tempviews[parseInt(order[4])-1];
		document.getElementById('view_'+order[5]).innerHTML = tempviews[parseInt(order[5])-1];
	} else if (current_view == 5) {
		$(views[parseInt(order[5])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[5]).innerHTML = tempviews[parseInt(order[5])-1];
	}
	setup();
	setupCloseSwap(order[1]);
	setupCloseSwap(order[2]);
	setupCloseSwap(order[3]);
	setupCloseSwap(order[4]);
	setupCloseSwap(order[5]);
	current_view = 6;
		
	height = $("#video_container").height();
	width = $("#video_container").width();

	$("#view_"+order[0]).width(width*0.34);
	$("#view_"+order[0]).height(height*0.5);
	$("#view_"+order[0]).offset({top: 30, left: 0});
	
	$("#view_"+order[1]).width(width*0.33);
	$("#view_"+order[1]).height(height*0.5);
	$("#view_"+order[1]).offset({top: 30, left: width*0.34});
	
	$("#view_"+order[2]).width(width*0.33);
	$("#view_"+order[2]).height(height*0.5);
	$("#view_"+order[2]).offset({top: 30, left: width*0.67});
	
	$("#view_"+order[3]).width(width*0.34);
	$("#view_"+order[3]).height(height*0.5);
	$("#view_"+order[3]).offset({top: 30 + height*0.5, left: 0});

	$("#view_"+order[4]).width(width*0.33);
	$("#view_"+order[4]).height(height*0.5);
	$("#view_"+order[4]).offset({top: 30 + height*0.5, left: width*0.34});

	$("#view_"+order[5]).width(width*0.33);
	$("#view_"+order[5]).height(height*0.5);
	$("#view_"+order[5]).offset({top: 30 + height*0.5, left: width*0.67});
}
function layout_7() {
	if (current_view == 1) {
		$(views[parseInt(order[1])-1]).appendTo('#video_container');
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[1]).innerHTML = tempviews[parseInt(order[1])-1];
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
	} else if (current_view == 2) {
		$(views[parseInt(order[2])-1]).appendTo('#video_container');
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[2]).innerHTML = tempviews[parseInt(order[2])-1];
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
	} else if (current_view == 3) {
		$(views[parseInt(order[3])-1]).appendTo('#video_container');
		document.getElementById('view_'+order[3]).innerHTML = tempviews[parseInt(order[3])-1];
	}
	setup();
	setupCloseSwap(order[1]);
	setupCloseSwap(order[2]);
	setupCloseSwap(order[3]);
	current_view = 7;
		
	height = $("#video_container").height();
	width = $("#video_container").width();

	$("#view_"+order[4]).remove();
	$("#view_"+order[5]).remove();

	$("#view_"+order[0]).width(width*0.75);
	$("#view_"+order[0]).height(height);
	$("#view_"+order[0]).offset({top: 30, left: 0});
	
	$("#view_"+order[1]).width(width*0.25);
	$("#view_"+order[1]).height(height*0.34);
	$("#view_"+order[1]).offset({top: 30, left: width*0.75});
	
	$("#view_"+order[2]).width(width*0.25);
	$("#view_"+order[2]).height(height*0.33);
	$("#view_"+order[2]).offset({top: 30 + height*0.34, left: width*0.75});
	
	$("#view_"+order[3]).width(width*0.25);
	$("#view_"+order[3]).height(height*0.33);
	$("#view_"+order[3]).offset({top: 30 + height*0.67, left: width*0.75});
}

function fix_layout() {
	if (current_view == 1) {
		layout_1();
	} else if (current_view == 2) {
		layout_2();
	} else if (current_view == 3) {
		layout_3();
	} else if (current_view == 4) {
		layout_4();
	} else if (current_view == 5) {
		layout_5();
	} else if (current_view == 6) {
		layout_6();
	} else if (current_view == 7) {
		layout_7();
	}

}

//Handle video swap
function swap(dragged, target) {

	var draggedView, draggedClose, draggedSwap, draggedOverlay, draggedNum,
		targetView, targetClose, targetSwap, targetOverlay, targetNum;

	if (dragged.attr('id') == "swap_1") {
		draggedNum = "1";
	} else	if (dragged.attr('id') == "swap_2") {
		draggedNum = "2";
	} else	if (dragged.attr('id') == "swap_3") {
		draggedNum = "3";
	} else	if (dragged.attr('id') == "swap_4") {
		draggedNum = "4";
	} else	if (dragged.attr('id') == "swap_5") {
		draggedNum = "5";
	} else	if (dragged.attr('id') == "swap_6") {
		draggedNum = "6";
	}

	if (target.attr('id') == "view_1") {
		targetNum = "1";
	} else if (target.attr('id') == "view_2") {
		targetNum = "2";
	} else if (target.attr('id') == "view_3") {
		targetNum = "3";
	} else if (target.attr('id') == "view_4") {
		targetNum = "4";
	} else if (target.attr('id') == "view_5") {
		targetNum = "5";
	} else if (target.attr('id') == "view_6") {
		targetNum = "6";
	}

	var draggedIndex = order.indexOf(draggedNum),
		targetIndex = order.indexOf(targetNum);
		
	var temp = order[draggedIndex];
	order[draggedIndex] = order[targetIndex];
	order[targetIndex] = temp;
	
	fix_layout();
	fix_layout();
	//fix_layout();
	
}

//Handle resize
$(window).resize(function(){
	fix_layout();
});

//First time startup configuration
function getUrlVars() {
	if (window.location.href.indexOf('?') == -1) {
		return null;
	} else {
		var vars = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
		return vars;
	}
}

setup();
layout_7();
current_view = 7;
// Start with video playing if given parameter

var tempitem = $('.startup');
if (tempitem.length != 0) {
	view1(tempitem);
}

// Startup config for Championship Event
tempitem = $('#cmp');
if (tempitem.length != 0) {
	layout_4();
	current_view = 4;

	view1($('#arc'));
	view2($('#cur'));
	view3($('#gal'));
	view4($('#new'));
}

});
