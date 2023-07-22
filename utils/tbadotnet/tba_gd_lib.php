<?php

/**
 * @param    $hex string        6-digit hexadecimal color
 * @return    array            3 elements 'r', 'g', & 'b' = int color values
 * @desc Converts a 6 digit hexadecimal number into an array of
 *       3 integer values ('r'  => red value, 'g'  => green, 'b'  => blue)
 */
function hex2int($hex) {
        return array( 'r' => hexdec(substr($hex, 0, 2)), // 1st pair of digits
                      'g' => hexdec(substr($hex, 2, 2)), // 2nd pair
                      'b' => hexdec(substr($hex, 4, 2))  // 3rd pair
                    );
}

/**
 * @param $input string     6-digit hexadecimal string to be validated
 * @param $default string   default color to be returned if $input isn't valid
 * @return string           the validated 6-digit hexadecimal color
 * @desc returns $input if it is a valid hexadecimal color, 
 *       otherwise returns $default (which defaults to black)
 */
function validHexColor($input = '000000', $default = '000000') {
    // A valid Hexadecimal color is exactly 6 characters long
    // and eigher a digit or letter from a to f
    return (eregi('^[0-9a-f]{6}$', $input)) ? $input : $default ;
}

function grad($im,$width, $height,$step,$basewidth,$baseheight,$end,$base)
{

    // from http://usalug.com/phpBB3//viewtopic.php?p=58019

	// $im is passed as @$im for the image to draw it on
	// $height is the Height of the box to draw
	// $width is the width of the box to draw
	// $step is the steps to take, a step of 10 would change the colour every 10 pixels
	// $baseheight is where to place the bottom of the rectangle
	// $basewidth is the right side of the location for the rectangle
	// $base is the start colour in hex (ffffff)
	// $end is the colour to end at in hex (000000)
	
	// Break colours into RGB components
	//sscanf($base, "%2x%2x%2x", $rbase, $gbase, $bbase);
	//sscanf($end, "%2x%2x%2x", $rend, $gend, $bend);
	
	$basecolors = hex2int($base);
	$rbase = $basecolors["r"];
	$gbase = $basecolors["g"];
	$bbase = $basecolors["b"];
	$endcolors = hex2int($end);
	$rend = $endcolors["r"];
	$gend = $endcolors["g"];
	$bend = $endcolors["b"];
	
	////////////////////////////////////////////////////
	// This color retrieval broken on server. replace with hex2int
	////////////////////////////////////////////////////
	
	// Set the Variable to step to use height
	//$varstep=$height;
	$varstep=$width;
	
	// Remove potential divide by 0 errors.
	if ($rbase==$rend) $rend = $rend -1;
	if ($gbase==$gend) $gend = $gend -1;
	if ($bbase==$bend) $bend = $bend -1;
	
	// Make sure the height is at least 1 pixel
	if ($varstep == 0) $varstep=1;
	
	// Set up step modifiers for each colour
	$rmod = ($rend - $rbase) /$varstep;
	$gmod = ($gend - $gbase) /$varstep;
	$bmod = ($bend - $bbase) /$varstep;
	
	// Serves no real purpose.
	$white=imagecolorallocate($im,255,255,255);
	
	// Loop for the height at a rate equal to the steps.
	for($i=1; $i<$varstep; $i=$i+$step+1)
	{
		//Adjust the colours
		$clour1 = ($i*$rmod)+$rbase;
		$clour2 = ($i*$gmod)+$gbase;
		$clour3 = ($i*$bmod)+$bbase;
		$col=imagecolorallocate($im,$clour1,$clour2,$clour3);
		
		//Paint the rectangle at current colour.
		//imagefilledrectangle ( resource $image, int $x1, int $y1, int $x2, int $y2, int $color )
		
		//This was breaking online because numbers out of range were being passed because I did a hacky job modifying this from vert to horiz originally. Fixed -gmm 092807
		
		$x1 = $basewidth-$i-1;
		$y1 = $baseheight-$height;
		$x2 = $basewidth-$i+$step-1;
		$y2 = $baseheight;
		imagefilledrectangle($im,$x1,$y1,$x2,$y2,$col);
	}

	// Return the image
	return $im; 
}

function imagettftextoutline(&$im,$size,$angle,$x,$y,&$col,&$outlinecol,$fontfile,$text,$width) {
    // For every X pixel to the left and the right
    for ($xc=$x-abs($width);$xc<=$x+abs($width);$xc++) {
        // For every Y pixel to the top and the bottom
        for ($yc=$y-abs($width);$yc<=$y+abs($width);$yc++) {
            // Draw the text in the outline color
            $text1 = imagettftext($im,$size,$angle,$xc,$yc,$outlinecol,$fontfile,$text);
        }
    }
    // Draw the main text
    $text2 = imagettftext($im,$size,$angle,$x,$y,$col,$fontfile,$text);
}

//NOT DONE
function imageStringoutline(&$im,$size,$x,$y,&$col,&$outlinecol,$text,$width) {
    // For every X pixel to the left and the right
    for ($xc=$x-abs($width);$xc<=$x+abs($width);$xc++) {
        // For every Y pixel to the top and the bottom
        for ($yc=$y-abs($width);$yc<=$y+abs($width);$yc++) {
            // Draw the text in the outline color
            $text1 = imageString($im,$size,$xc,$yc,$text,$outlinecol);
        }
    }
    // Draw the main text
    $text2 = imageString($im,$size,$x,$y,$text,$col);
}

function tba_api_request($path) {
	global $key;
	// TODO: Use curl instead?
	$json = file_get_contents(
		"https://www.thebluealliance.com/api/v3/$path?X-TBA-Auth-Key=$key"
	);
	return json_decode($json, true);
}
