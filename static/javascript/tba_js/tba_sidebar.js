$(document).ready(function(){
  $(document.body).scrollspy({
    target: '.tba-sidebar',
    offset: $('.navbar').outerHeight(true) + 10
  });
});
