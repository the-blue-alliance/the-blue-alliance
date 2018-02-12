<?php

include __DIR__ . '/config.php';

include("tba_gd_lib.php");
error_reporting(E_ALL ^ E_NOTICE ^ E_STRICT);

function sanatizeGet($value) {
	$output = htmlentities(stripslashes($value));
	return $output;
}

function eventSort($event_a, $event_b) {
    $a_start = $event_a["start_date"];
    $b_start = $event_b["start_date"];
    if ($a_start == $b_start) {
        return 0;
    }
    return ($a_start < $b_start) ? -1 : 1;
}

function mergeWLT($a, $b) {
	$a['losses'] += $b['losses'];
	$a['ties'] += $b['ties'];
	$a['wins'] += $b['wins'];
	return $a;
}

function stringWLT($wlt) {
	return "({$wlt['wins']}-{$wlt['losses']}-{$wlt['ties']})";
}

function getTeamDetails($teamnumber, $year) {
	$data = tba_api_request("team/frc$teamnumber/simple");
    // TODO: International teams?
    $data['location'] = "{$data['city']}, {$data['state_prov']}";
    $data['events'] = tba_api_request("team/frc$teamnumber/events/$year");
    foreach ($data['events'] as &$event) {
    	$start = strtotime($event['start_date']);
    	if (time() < $start) {
    		// Hasn't started yet
			continue;
		}
		$event['status'] = $status = tba_api_request("team/frc$teamnumber/event/{$event['key']}/status");
    	if (isset($status['playoff'])) {
    		$event['wlt'] = mergeWLT($status['playoff']['record'], $status['qual']['ranking']['record']);
    		if ($status['playoff']['status'] == 'won') {
    			$event['finish'] = 'Champions';
			} else {
    			switch ($status['playoff']['level']) {
					case 'f':
						$event['finish'] = 'Finalists';
						break;
					case 'sf':
						$event['finish'] = 'Semifinalists';
						break;
					case 'qf':
						$event['finish'] = 'Quarterfinalists';
						break;
					default:
						// ???
						$event['finish'] = '';
						break;
				}
			}
		} else {
    		$event['wlt'] = $status['qual']['record'];
    		$event['finish'] = '';
		}

	}
	return $data;
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
	if (!$grad) {
		throw new RuntimeException('imageCreateTrueColor failed');
	}
	imageAlphaBlending($grad, TRUE);
	
	// Step 2. Set background gradient up
	grad($grad, 470, 70, 2, 470, 70, $start_color,$stop_color);
	
	//Get the overlay in, copy it, and destroy it.
	$baseline = imageCreateFromPNG('baseline.png');
	imageCopy($grad, $baseline, 0, 0, 0, 0, 470, 70);
	imageDestroy($baseline);
	
	//save it
	$saved = imagePNG($grad,"gradients/from" . $start_color . "to" . $stop_color . ".png");
	if (!$saved) {
		throw new RuntimeException('imagepng failed');
	}
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
	
	$yearWLT = array('losses' => 0, 'ties' => 0, 'wins' => 0);
	
	imageStringoutline($teamoverlay,3,8,5,$white,$black,$teamstring,1);
	imagettftextoutline($teamoverlay,6,0,$location_offset,16,$negwhite,$negblack,__DIR__ . '/slkscr.ttf',$team["location"],1);
	
	if (count($team["events"]) > 4) {
		$event_text_offset = 27;
	} else {
		$event_text_offset = 30; //18 for imageStringOutline, 30 for TTF
	}
	if ($team["events"]) {
	    usort($team["events"], "eventSort");
	    $events = $team['events'];
		$firstColEventLen = 0;
		$secondColEventLen = 0;
		$eventsCounted = 0;
		foreach($events as $event) {
			$eventsCounted++;
			if ($eventsCounted > 5) {
				$secondColEventLen = max($secondColEventLen, strlen($event['short_name']));
			} else {
				$firstColEventLen = max($firstColEventLen, strlen($event['short_name']));
			}
		}
		$secondPx = intval($firstColEventLen * 7);
		$firstPx = 18;
		$eventsDone = 0;
		foreach($events as $event) {
			$eventsDone++;
			if (isset($event['status'])) {
				$eventWLT = stringWLT($event['wlt']);
				imagettftextoutline($teamoverlay,6,0,$firstPx,$event_text_offset,$negwhite,$negblack,__DIR__ . '/slkscr.ttf',"{$event['short_name']}:",1);
				imagettftextoutline($teamoverlay,6,0,$secondPx,$event_text_offset,$negwhite,$negblack,__DIR__ . '/slkscr.ttf',"{$eventWLT} {$event['finish']}",1);
			} else {
				//event happens in future, or team didn't really play at event
				imagettftextoutline($teamoverlay,6,0,$firstPx,$event_text_offset,$negwhite,$negblack,__DIR__ . '/slkscr.ttf',"{$event['short_name']}:",1);
				$start_date = strtotime($event["start_date"]);
				$pretty_start_date = date("F j, Y", $start_date);
				imagettftextoutline($teamoverlay,6,0,$secondPx,$event_text_offset,$negwhite,$negblack,__DIR__ . '/slkscr.ttf',$pretty_start_date,1);
			}
		    $event_text_offset = $event_text_offset + 10; //+12 for imageStringOutline, 10 for TTF
			$yearWLT = mergeWLT($yearWLT, $event['wlt']);
			if ( $eventsDone == 5 ) {
				// Second column
				$firstPx = $secondPx + 100;
				$secondPx = $firstPx + intval($secondColEventLen * 5.2);
				$event_text_offset = 27;
			}
	    }
	}

	$yearWLTstr = stringWLT($yearWLT);
	imageStringoutline($teamoverlay,3,295,53,$white,$black,"$year Record: $yearWLTstr",1);
	
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
