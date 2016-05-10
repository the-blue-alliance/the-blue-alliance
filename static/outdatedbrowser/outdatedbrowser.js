/* Based on code from outdatedbrowser.com */

var outdatedBrowser = function(options) {

  var MIN_IE_VERSION = 10;

  var IE = function() {
    var ua = window.navigator.userAgent;

    var msie = ua.indexOf('MSIE ');
    if (msie > 0) {
      // IE 10 or older => return version number
      return parseInt(ua.substring(msie + 5, ua.indexOf('.', msie)), 10);
    }

    var trident = ua.indexOf('Trident/');
    if (trident > 0) {
      // IE 11 => return version number
      var rv = ua.indexOf('rv:');
      return parseInt(ua.substring(rv + 3, ua.indexOf('.', rv)), 10);
    }

    var edge = ua.indexOf('Edge/');
    if (edge > 0) {
      // Edge (IE 12+) => return version number
      return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10);
    }
  }

  if (IE() && IE() < MIN_IE_VERSION) {
    showUpdateMessage();
  }

  function showUpdateMessage() {
    var outdated = document.getElementById("outdated");
    var btnClose = document.getElementById("btnCloseUpdateBrowser");
    var btnUpdate = document.getElementById("btnUpdateBrowser");

    // Show the update message
    outdated.className = 'visible';

    // Setup close button
    btnClose.onmousedown = function() {
      outdated.className = '';
      return false;
    };

    // Override the update button color to match the background color
    btnUpdate.onmouseover = function() {
      this.style.color = bgColor;
      this.style.backgroundColor = txtColor;
    };
    btnUpdate.onmouseout = function() {
      this.style.color = txtColor;
      this.style.backgroundColor = bgColor;
    };
  }
};
