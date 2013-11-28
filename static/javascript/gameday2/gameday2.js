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
        <GamedayNavbar />
        <WebcastAddButton onWebcastAdd={this.handleWebcastAdd} />
        <VideoGrid data={this.state.data} />
      </div>
    );
  }
});

var GamedayNavbar = React.createClass({
  render: function() {
    return (
      <div className="navbar navbar-default navbar-fixed-top">
        <div className="gameday-container">
          <div className="brand gameday-brand pull-left">
            <span className="gameday-title">TBA GameDay</span>
            <a className="main-site" href="/">To main site &raquo;</a>
            <div className="div_helper"></div>
          </div>

          <ul className="nav navbar-nav pull-right">
            <li className="dropdown">
              <a className="dropdown-toggle" href="#">Layouts</a>
              <ul className="dropdown-menu">
                <li><a className="layout-choice layout_0" href="javascript:layout_0()">Single View</a></li>
                <li><a className="layout-choice layout_1" href="javascript:layout_1()">Split View</a></li>
                <li><a className="layout-choice layout_2" href="javascript:layout_2()">1+2 View</a></li>
                <li><a className="layout-choice layout_3" href="javascript:layout_3()">Quad View</a></li>
                <li><a className="layout-choice layout_6" href="javascript:layout_6()">1+3 View</a></li>
                <li><a className="layout-choice layout_4" href="javascript:layout_4()">1+4 View</a></li>
                <li><a className="layout-choice layout_5" href="javascript:layout_5()">Hex View</a></li>
              </ul>
            </li>
            
            <li className="dropdown">
              <a className="dropdown-toggle" href="#">Webcasts</a>
              <ul className="dropdown-menu webcasts">
                <li><a>No webcasts</a></li>
              </ul>
            </li>
            
            <li className="dropdown">
              <a className="dropdown-toggle" href="#">Results</a>
              <ul className="dropdown-menu results">
                <li><a>No events</a></li>
              </ul>
            </li>
            
            <li className="social"><a className="social-toggle" href="javascript:social_tab();">Social Feed</a></li>
            <li className="chat"><a className="chat-toggle" href="javascript:chat_tab();">Chat</a></li>
            <li className="settings"><a className="settings-button" href="#settings-modal" data-toggle="modal"><span className="glyphicon glyphicon-cog"></span></a></li>
          </ul>
        </div>
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