$(document).ready(function(){
  // Remove blank fields
  $('#event-filter-form').submit(function() {
    $(this).find('select').each(function () {
      if ($(this).val() == '') {
        $(this).prop('disabled', true);
      }
    });

    if ($('#event-filter-postalcode').val() == '') {
      $('#event-filter-postalcode').prop('disabled', true);
      $('#event-filter-range').prop('disabled', true);
    }
  });

  // Show/Hide range based on postal code input
  if ($('#event-filter-postalcode').val() == '') {
    $('#event-filter-range').hide();  // Start hidden if blank
  }
  $('#event-filter-postalcode').on('change keyup paste mouseup', function () {
    if ($(this).val() == '') {
      $('#event-filter-range').fadeOut(100);
    } else {
      $('#event-filter-range').fadeIn(100);
    }
  });
});
