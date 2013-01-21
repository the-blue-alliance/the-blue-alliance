// Charts
$(function() {
	// Single Bar Graph
	var chartsData = $(".xcharts-bar-single-data");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw = JSON.parse($('#' + chartId).html())
		var data = [];
		for (var key in raw) {
			var value = raw[key];
			data = data.concat([{"x": parseInt(key), "y": value}]);
		}
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "bar",
						 "main": [{"className": "." + chartId + '-elements',
							 	   "data": data}],
						 }
		var opts = {"tickFormatY": function(y){ return y + "%"; }};
		var myChart = new xChart('bar', chartData, '#' + chartId + '-chart', opts);
	}
	
	// Single Line Graph
	var chartsData = $(".xcharts-line-single-data");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw = JSON.parse($('#' + chartId).html());
		var data = [];
		for (var key in raw) {
			var tuple = raw[key];
			data = data.concat([{"x": tuple[0], "y": tuple[1]}]);
		}
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "line-dotted",
						 "main": [{"className": "." + chartId + '-elements',
							 	   "data": data}],
						 }
		var myChart = new xChart('line', chartData, '#' + chartId + '-chart');
	}
	
	// Double Line Graph
	var chartsData = $(".xcharts-line-double-data");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw = JSON.parse($('#' + chartId).html());
		var dataA = [];
		var dataB = [];
		var xLabels = []
		var indexA = 0;
		for (var key in raw[0]) {
			var tuple = raw[0][key];
			dataA = dataA.concat([{"x": indexA, "y": tuple[1]}]);
			xLabels = xLabels.concat([tuple[0]]);
			indexA += 1;
		}
		var indexB = 0;
		for (var key in raw[1]) {
			var tuple = raw[1][key];
			dataB = dataB.concat([{"x": indexB, "y": tuple[1]}]);
			indexB += 1;
		}
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "line-dotted",
						 "main": [{"className": "." + chartId + '-elements',
							 	   "data": dataA},
							 	  {"className": "." + chartId + '-elements',
								   "data": dataB}],
						 }
		var opts = {
		  "tickFormatX": function (x) { return xLabels[x]; }
		}
		var myChart = new xChart('line', chartData, '#' + chartId + '-chart', opts);
	}
	
	
	// Double Bar Graph
	var chartsData = $(".xcharts-bar-double-data");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw = JSON.parse($('#' + chartId).html())
		var dataA = [];
		var dataB = [];
		for (var key in raw[0]) {
			var value = raw[0][key];
			dataA = dataA.concat([{"x": parseInt(key), "y": value}]);
		}
		for (var key in raw[1]) {
			var value = raw[1][key];
			dataB = dataB.concat([{"x": parseInt(key), "y": value}]);
		}
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "bar",
						 "main": [{"className": "." + chartId + '-elements',
							 	   "data": dataA},
							 	  {"className": "." + chartId + '-elements',
								   "data": dataB}],
						 }
		var opts = {"tickFormatY": function(y){ return y + "%"; }};
		var myChart = new xChart('bar', chartData, '#' + chartId + '-chart', opts);
	}
});
