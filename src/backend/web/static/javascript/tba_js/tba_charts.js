// Charts
$(function() {
	// Line Graph
	var chartsData = $(".xcharts-line-data");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw_datasets = JSON.parse($('#' + chartId).html());
		var datasets = [];
		var xLabels = [];
		
		for (var j=0; j < raw_datasets.length; j++) {
		  var raw_dataset = raw_datasets[j];
		  var dataset = []
		  for (var k=0; k < raw_dataset.length; k++) {
		    var tuple = raw_dataset[k];
        if (i == 0) {  // Generate x-axis labels from first raw datset
          xLabels = xLabels.concat([tuple[0]]);
        }
        dataset = dataset.concat([{"x": k, "y": tuple[1]}]);
		  }
		  datasets = datasets.concat([dataset]);
		}
		
		var main = [];
		for (var j=0; j < datasets.length; j++) {
		  main = main.concat({"className": "." + chartId + '-elements',
                          "data": datasets[j]});
		}
		
		var chartData = {
	    "xScale": "ordinal",
      "yScale": "linear",
			"type": "line-dotted",
			"main": main
		};
		var opts = {
		  "tickFormatX": function (x) { return xLabels[x]; }
		};
		var myChart = new xChart('line', chartData, '#' + chartId + '-chart', opts);
	}
	
	
	// Bar Graph
	var chartsData = $(".xcharts-bar-data");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw_datasets = JSON.parse($('#' + chartId).html());
		var datasets = [];
		
    for (var j=0; j < raw_datasets.length; j++) {
      var raw_dataset = raw_datasets[j];
      var dataset = []
      for (var key in raw_dataset) {
        var value = raw_dataset[key];
        dataset = dataset.concat([{"x": parseInt(key), "y": value}]);
      }
      datasets = datasets.concat([dataset]);
    }
    
    var main = [];
    for (var j=0; j < datasets.length; j++) {
      main = main.concat({"className": "." + chartId + '-elements',
                          "data": datasets[j]});
    }
		
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "bar",
						 "main": main
						 };
		var opts = {"tickFormatY": function(y){ return y + "%"; }};
		var myChart = new xChart('bar', chartData, '#' + chartId + '-chart', opts);
	}
});
