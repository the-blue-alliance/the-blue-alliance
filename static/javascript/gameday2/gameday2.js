/** @jsx React.DOM */
var GamedayFrame = React.createClass({
  loadDataFromServer: function() {
    $.ajax({
      url: this.props.url,
      success: function(data) {
        this.setState({data: data});
      }.bind(this)
    });
  },
  handleWebcastAdd: function(webcast) {
    var webcasts = this.state.data;
    var newWebcasts = webcasts.concat([webcast]);
    this.setState({data: newWebcasts});
    $.ajax({
      url: this.props.url,
      type: 'POST',
      data: webcast,
      success: function(data) {
        this.setState({data: data});
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: []};
  },
  componentWillMount: function() {
    //this.loadDataFromServer();
    //setInterval(this.loadDataFromServer, this.props.pollInterval);
    this.setState({data: this.props.data})
  },
  render: function() {
    return (
      <div className="gameday">
        <h1>Gameday!</h1>
        <WebcastAddButton onWebcastAdd={this.handleWebcastAdd} />
        <VideoGrid data={this.state.data} />
      </div>
    );
  }
});

var VideoGrid = React.createClass({
  render: function() {
    var videoCellNodes = this.props.data.map(function (video) {
      return <VideoCell embed={video.embed} event_name={video.event_name} />;
    });
    return (
      <div className="videoGrid">
        {videoCellNodes}
      </div>
    );
  }
});

var VideoCell = React.createClass({
  render: function() {
    return (
      <div className="videoCell">
        <h3>{this.props.event_name}</h3>
        <iframe width="560" height="315" src={this.props.embed} frameBorder="0" allowFullScreen></iframe>
      </div>
    );
  }
});

var WebcastAddButton = React.createClass({
  handleClick: function() {
    var embed = "//www.youtube.com/embed/qwaptht9WYg?rel=0";
    var event_name = "New Event!";
    this.props.onWebcastAdd({embed: embed, event_name: event_name});
    return false;
  },
  render: function() {
    return (
      <a href="#" onClick={this.handleClick}>Add Webcast</a>
    )
  }
})

var data = [
  {"embed": "//www.youtube.com/embed/olhwB5grOtA?rel=0", "event_name": "BAE Granite State"},
  {"embed": "//www.youtube.com/embed/OtAZ4_Nh3CY?rel=0", "event_name": "UTC Regional"}
]

React.renderComponent(
  <GamedayFrame data={data} pollInterval={20000} />,
  document.getElementById('content')
);