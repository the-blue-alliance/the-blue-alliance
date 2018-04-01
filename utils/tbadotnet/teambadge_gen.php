<?PHP

include("tba_gd_lib.php");
error_reporting(E_ALL ^ E_NOTICE ^ E_STRICT);

function sanatizeGet($value) {
	$output = htmlentities(stripslashes($value));
	return $output;
}

function eventSort($event_a, $event_b) {
    $a_start = strtotime($event_a["start_time"]);
    $b_start = strtotime($event_b["start_time"]);
    if ($a_start == $b_start) {
        return 0;
    }
    return ($a_start < $b_start) ? -1 : 1;
}

function getTeamDetails($teamnumber, $year) {
    $json = file_get_contents("http://www.thebluealliance.com/api/v1/team/details?events=1&team=frc".$teamnumber."&year=".$year);
    return json_decode($json, TRUE);
}

if ($_REQUEST['debug'] == 1) {
	$start_time = microtime(TRUE);
	$regen_overlay = $_REQUEST['regen'];
}

$start_color = sanatizeGet(strtoupper($_REQUEST['start']));
$stop_color = sanatizeGet(strtoupper($_REQUEST['stop']));
$teamnumber = sanatizeGet(stripslashes($_REQUEST["team"]));
$teamnumber = ltrim($teamnumber, '0');
if (!is_numeric($teamnumber)) die('team number non numeric. Team number was \''.$teamnumber.'\'');

//if the gradient background doesn't exist, make it.
if (!file_exists("gradients/from" . $start_color . "to" . $stop_color . ".png")) {
	$grad = imageCreateTrueColor(470,70);
	imageAlphaBlending($grad, TRUE);
	
	// Step 2. Set background gradient up
	grad($grad, 470, 70, 2, 470, 70, $start_color,$stop_color);
	
	//Get the overlay in, copy it, and destroy it.
	$baseline = imageCreateFromPNG('baseline.png');
	imageCopy($grad, $baseline, 0, 0, 0, 0, 470, 70);
	imageDestroy($baseline);
	
	//save it
	imagePNG($grad,"gradients/from" . $start_color . "to" . $stop_color . ".png");
	//kill it
	imageDestroy($grad);
}

if (!file_exists("teamoverlays/team" . $teamnumber . ".png")) {
	$regen_overlay = 1;
}
elseif ((time() - filemtime("teamoverlays/team" . $teamnumber . ".png") > 86400)) {
	$regen_overlay = 1;
	unlink("teamoverlays/team" . $teamnumber . ".png"); //delete old version
}

if ($regen_overlay == 1) {
//file doesn't exist or is over one day old.

	$teamoverlay = imageCreateTrueColor(470,70);
	imageSaveAlpha($teamoverlay, true);
	imageAlphaBlending($teamoverlay, true);
	$transparentColor = imagecolorallocatealpha($teamoverlay, 200, 200, 200, 127);
	imagefill($teamoverlay, 0, 0, $transparentColor);

	//set up colors
	$white = imagecolorallocate($teamoverlay,255,255,255);
	$negwhite = 0 - $white;
	$black = imagecolorallocate($teamoverlay,0,0,0);
	$negblack = 0 - $black;
	
	$year = date('Y');	
	$team = getTeamDetails($teamnumber, $year);
	
	$teamstring = "Team $teamnumber";
	if ($team["nickname"] != "") {
		$teamstring = $teamstring . " - {$team["nickname"]}";
	}
	
	$location_offset = imageFontWidth(3) * strlen($teamstring) + 15;
	
	$yearWLT = ""; //TODO: Reimplement WLT
	
	imageStringoutline($teamoverlay,3,8,5,$white,$black,$teamstring,1);
	imagettftextoutline($teamoverlay,6,0,$location_offset,16,$negwhite,$negblack,'slkscr.ttf',$team["location"],1);
	
	if (count($team["events"]) > 4) {
		$event_text_offset = 27;
	} else {
		$event_text_offset = 30; //18 for imageStringOutline, 30 for TTF
	}
	
	if ($team["events"]) {
	    usort($events = $team["events"], "eventSort");
	    foreach($events as $event) {
	    //if ($eventWLT != "(0-0-0)") {
		//	$highestmatch = getHighestMatch($eventid, "string", $teamnumber);
		//	$eventranking = "";
		//	if ($highestmatch != "Participants" AND $highestmatch != "") {
		//		$eventranking = " - $highestmatch";
		//	}
		//	// TTF processing is not doing "silkscreen" N and M correctly in GD 2.0.28. Fixed in 2.0.35. Waiting for PHP to incorporate updated library.
		//	imagettftextoutline($teamoverlay,6,0,18,$event_text_offset,$negwhite,$negblack,'slkscr.ttf',"$eventshort:",1);
		            //imagettftextoutline($teamoverlay,6,0,90,$event_text_offset,$negwhite,$negblack,'slkscr.ttf',"{$eventWLT}{$eventranking}",1);
		//} else {
		//event happens in future, or team didn't really play at event
		imagettftextoutline($teamoverlay,6,0,18,$event_text_offset,$negwhite,$negblack,'slkscr.ttf',"{$event["short_name"]}:",1);
		   $start_date = strtotime($event["start_date"]);
		   $pretty_start_date = date("F j, Y", $start_date);
		    imagettftextoutline($teamoverlay,6,0,90,$event_text_offset,$negwhite,$negblack,'slkscr.ttf',$pretty_start_date,1);
		//}
		    $event_text_offset = $event_text_offset + 10; //+12 for imageStringOutline, 10 for TTF
	    }
	}
	
	//imageStringoutline($teamoverlay,3,295,53,$white,$black,"$year Record: $yearWLT",1);
	
	//save it
	imagePNG($teamoverlay,"teamoverlays/team" . $teamnumber . ".png");
	//kill it
	imageDestroy($teamoverlay);
}

// Step 1. Create a new blank image
$im = imageCreateTrueColor(470,70);
imageAlphaBlending($im, TRUE);

//Get the whole background layer in, copy it, and destroy it.
$background = imageCreateFromPNG("gradients//from" . $start_color . "to" . $stop_color . ".png");
imageCopy($im, $background, 0, 0, 0, 0, 470, 70);
imageDestroy($background); 

//Get the whole team overlay layer in, copy it, and destroy it.
$statsoverlay = imageCreateFromPNG("teamoverlays/team" . $teamnumber . ".png");
imageCopy($im, $statsoverlay, 0, 0, 0, 0, 470, 70);
imageDestroy($statsoverlay); 

//debug output time
if ($_REQUEST['debug'] == 1) {

	//set up colors
	$white = imagecolorallocate($im,255,255,255);
	$negwhite = 0 - $white;
	$black = imagecolorallocate($im,0,0,0);
	$negblack = 0 - $black;

	$stop_time = microtime(TRUE);
	$time = $stop_time - $start_time;
	imageStringoutline($im,3,295,13,$white,$black,$time,1);
}

// Step 3. Send the headers (at last possible time)
header('Content-type: image/png');

// Step 4. Output the image as a PNG 
imagePNG($im);

// Step 5. Delete the image from memory
imageDestroy($im);


?>