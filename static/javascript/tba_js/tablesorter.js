$(document).ready(function(){
    // add parser through the tablesorter addParser method
    $.tablesorter.addParser({
        // set a unique id
        id: 'wlt',
        is: function(s) {
        // return false so this parser is not auto detected
            return false;
        },
        format: function(s) {
            // format your data for normalization
            s = parseFloat(s);
        return s;
        },
        // set type, either numeric or text
        type: 'numeric'
    });
    $("#rankingsTable").tablesorter({
        headers: {
            7: { sorter:'wlt' }
        },
        sortList: [[0,0]],
        textExtraction:'complex'
    });
});