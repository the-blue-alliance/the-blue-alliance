/** @jsx React.DOM */
var GamedayFrame = React.createClass({
  loadDataFromServer: function() {
    $.ajax({
      url: this.props.url,
      success: function(events) {
        this.setState({events: events});
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {
      events: [],
      displayedEvents: []
    };
  },
  componentWillMount: function() {
    //this.loadDataFromServer();
    //setInterval(this.loadDataFromServer, this.props.pollInterval);
    this.setState({events: this.props.events})
  },
  render: function() {
    return (
      <div className="gameday container-full">
        <GamedayNavbar 
          events={this.state.events}
          onWebcastAdd={this.handleWebcastAdd}
          onWebcastReset={this.handleWebcastReset} />
        <VideoGrid events={this.state.displayedEvents} />
      </div>
    );
  },
  handleWebcastAdd: function(eventModel) {
    var displayedEvents = this.state.displayedEvents;
    var newDisplayedEvents = displayedEvents.concat([eventModel]);
    this.setState({displayedEvents: newDisplayedEvents});
  },
  handleWebcastReset: function() {
    this.setState({displayedEvents: []});
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
            <WebcastDropdown
              events={this.props.events}
              onWebcastAdd={this.props.onWebcastAdd}
              onWebcastReset={this.props.onWebcastReset} />
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
    var videoCellNodes = this.props.events.map(function (eventModel) {
      return (
        <VideoCell
          eventModel={eventModel}
          onDrop={this.handleDrop} />
        );
    });
    return (
      <div className="videoGrid">
        {videoCellNodes}
      </div>
    );
  },
});

var VideoCell = React.createClass({
  componentDidMount: function () {
    $(this.getDOMNode()).fitVids();
  },
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
        <div className="fitvids">
          <iframe width="560" height="315" src={src} frameBorder="0" allowFullScreen></iframe>
        </div>
      </div>
    );
  }
});

var WebcastDropdown = React.createClass({
  render: function() {
    var webcastListItems = [];
    for (var index in this.props.events) {
      webcastListItems.push(<WebcastListItem eventModel={this.props.events[index]} onWebcastAdd={this.props.onWebcastAdd} />)
    };
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Webcasts <b className="caret"></b></a>
        <ul className="dropdown-menu">
          {webcastListItems}
          <li className="divider"></li>
          <BootstrapNavDropdownListItem handleClick={this.props.onWebcastReset}>Reset Webcasts</BootstrapNavDropdownListItem>
        </ul>
      </li>
    );    
  }
})

var WebcastListItem = React.createClass({
  handleClick: function() {
    this.props.onWebcastAdd(this.props.eventModel);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.eventModel.name}</BootstrapNavDropdownListItem>
  },
})

var BootstrapNavDropdownListItem = React.createClass({
  componentWillMount: function() {
    if (!this.props.a) {
      this.props.a = "#";
    }
  },
  handleClick: function() {
    if (this.props.handleClick) {
      this.props.handleClick();
      return false;
    }
  },
  render: function() {
    return (
      <li><a href="{this.props.a}" onClick={this.handleClick}>{this.props.children}</a></li>
    )
  },
})

var events = [
  {"key": "2014nh", "name": "BAE Granite State", "webcasts": [{"type": "youtube", "channel": "olhwB5grOtA"}]},
  {"key": "2014ct", "name": "UTC Regional", "webcasts": [{"type": "youtube", "channel": "FKpIWmsDPq4"}]},
  {"key": "2014az", "name": "Arizona!", "webcasts": [{"type": "youtube", "channel": "QZv70PG9eXM"}]}
]

React.renderComponent(
  <GamedayFrame events={events} pollInterval={20000} />,
  document.getElementById('content')
);