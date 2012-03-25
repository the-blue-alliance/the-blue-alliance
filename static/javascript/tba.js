window.onscroll = scrollheader;

function scrollheader() {
    var scrollx = document.body.scrollLeft
    var header = document.getElementById('topHeader')
    header.style.left = 0-scrollx+'px'
}