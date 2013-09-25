// General JS for all pages
$(document).ready(function(){
	// Jumping to page section
  $('.smooth-scroll').bind('click',function(event){
    var $anchor = $(this);
    var $navbar_position = $('.navbar').css('top');
    var $navbar_height = parseInt($('.navbar').css('height'));
    var $offset = 0;
    
    // Takes care of changing navbar size/position due to @media width
    if ($navbar_position == '0px') {
      $offset = $navbar_height + 10;
    }
    
    var target_offset = $($anchor.attr('href')).offset();
    if (target_offset == null) {
      var pixels = 0;
    } else {
      var pixels = target_offset.top - $offset;
    }
  
    $('html, body').stop().animate({
        scrollTop: pixels
    }, 250);
    event.preventDefault();
  });
	
	// Fancybox
	$(".fancybox").fancybox();
	
	// Tooltips
  $("[rel=tooltip]").tooltip();
  $("[rel=tooltip-bottom]").tooltip({placement: 'bottom'});
	
	// Fitvids
	$('.fitvids').fitVids();

	// JWPlayer
	if ($("#tbavideo_container").length != 0) {
    jwplayer("tbavideo_container").setup({
      players: [
          { type: "flash", src: "/jwplayer/player.swf" },
          { type: "html5" }
      ],
      provider: "http",
      controlbar: "bottom",
    });
	}
});
