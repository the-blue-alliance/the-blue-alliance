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
    return (
      <div className="videoGrid">
        <table width="100%">
          <tr>
            <td>
              <VideoCell eventModel={this.props.data[0]} />
            </td>
          </tr>
          <tr>
            <td><VideoCell eventModel={this.props.data[1]} /></td>
            <td><VideoCell eventModel={this.props.data[2]} /></td>
            <td><VideoCell eventModel={this.props.data[3]} /></td>
          </tr>
        </table>
      </div>
    );
  }
});

var VideoCell = React.createClass({
  render: function() {
    if (this.props.eventModel) {
      if (this.props.eventModel.webcasts) {
        var src = "//www.youtube.com/embed/" + this.props.eventModel.webcasts[0].channel;
      }
    } else {
      var src = "";
    }
    return (
      <div className="videoCell">
        <h3>{this.props.name}</h3>
        <iframe width="560" height="315" src={src} frameBorder="0" allowFullScreen></iframe>
      </div>
    );
  }
});

var WebcastAddButton = React.createClass({
  handleClick: function() {
    var key = "2014az";
    var name = "Arizona!";
    var webcasts = [{"type": "youtube", "channel": "QZv70PG9eXM"}];
    this.props.onWebcastAdd({key: key, name: name, webcasts: webcasts});
    return false;
  },
  render: function() {
    return (
      <a href="#" className="btn btn-default" onClick={this.handleClick}>Add Webcast</a>
    )
  }
})

var data = [
  {"key": "2014nh", "name": "BAE Granite State", "webcasts": [{"type": "youtube", "channel": "olhwB5grOtA"}]},
  {"key": "2014ct", "name": "UTC Regional", "webcasts": [{"type": "youtube", "channel": "OtAZ4_Nh3CY"}]}
]

React.renderComponent(
  <GamedayFrame data={data} pollInterval={20000} />,
  document.getElementById('content')
);