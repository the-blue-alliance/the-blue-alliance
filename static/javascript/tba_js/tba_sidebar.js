$(document).ready(function(){
  $("body").bind("DOMSubtreeModified", function() {
      $(document.body).scrollspy({
      target: '.tba-sidebar',
      offset: $('.navbar').outerHeight(true) + 10
    });
  });
});
