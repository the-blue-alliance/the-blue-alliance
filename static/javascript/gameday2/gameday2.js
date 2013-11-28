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
      <div className="gameday container">
        <GamedayNavbar onWebcastAdd={this.handleWebcastAdd} />
        <VideoGrid data={this.state.data} />
      </div>
    );
  }
});

var GamedayNavbar = React.createClass({
  render: function() {
    return (
      <nav className="navbar navbar-default navbar-fixed-top" role="navigation">
        <div className="navbar-header">
          <button type="button" className="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
            <span className="sr-only">Toggle navigation</span>
            <span className="icon-bar"></span>
            <span className="icon-bar"></span>
            <span className="icon-bar"></span>
          </button>
          <a className="navbar-brand" href="#">Gameday</a>
        </div>

        <div className="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul className="nav navbar-nav navbar-right">
            <li><WebcastAddButton onWebcastAdd={this.props.onWebcastAdd} /></li>
            <li className="dropdown">
              <a href="#" className="dropdown-toggle" data-toggle="dropdown">Layouts <b className="caret"></b></a>
              <ul className="dropdown-menu">
                <li><a href="#">First</a></li>
                <li><a href="#">Second</a></li>
                <li><a href="#">Third</a></li>
                <li className="divider"></li>
                <li><a href="#">Separated link</a></li>
              </ul>
            </li>
            <li className="dropdown">
              <a href="#" className="dropdown-toggle" data-toggle="dropdown">Webcasts <b className="caret"></b></a>
              <ul className="dropdown-menu">
                <li><a href="#">First</a></li>
                <li><a href="#">Second</a></li>
                <li><a href="#">Third</a></li>
                <li className="divider"></li>
                <li><a href="#">Separated link</a></li>
              </ul>
            </li>
            <li><a href="#" className="btn btn-default">Chat</a></li>
            <li><a href="#" className="btn btn-default">Hashtags</a></li>
            <li><a href="#">Settings</a></li>
          </ul>
        </div>
      </nav>
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
      <div className="videoCell ui-droppable">
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
      <a href="#" className="btn btn-default" onClick={this.handleClick}>Add Webcast</a>
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