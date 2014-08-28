$(document).ready(function(){
  $(document.body).scrollspy({
    target: '.tba-sidebar',
    offset: $('.navbar').outerHeight(true) + 10
  });
  $("body").bind("DOMSubtreeModified", function() {
    refreshScrollspyThrottled();
  });

  $('.tba-sidebar-collapsed').on('activate.bs.scrollspy', function() {
    $('.tba-sidenav').find('ul').each(function() {
      if ($(this).parent().hasClass('active')) {
        $(this).removeClass('hide');
      } else {
        $(this).addClass('hide');
      }
    });
  });
});

var isThrottled = false,
    throttleDuration = 500; // ms

function refreshScrollspyThrottled() {
  if (!isThrottled) {
    isThrottled = true;
    setTimeout(function () { isThrottled = false; }, throttleDuration);
    $(document.body).scrollspy('refresh');
  }
}
