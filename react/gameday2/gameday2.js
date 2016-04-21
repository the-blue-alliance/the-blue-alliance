var React = require('react');
var ReactDOM = require('react-dom');
var classNames = require('classnames');
var _ = require('underscore');

var GamedayFrame = React.createClass({
  getInitialState: function() {
    return {
      chatEnabled: false,
      displayedWebcasts: [],
      webcasts: [],
      followingTeams: [177,230],
      hashtagEnabled: false,
    };
  },
  componentWillMount: function() {
    // Process webcast data
    // Special and event webcasts are normalized into objects with 6 attributes:
    // key, num, id, name, type, and channel
    var webcasts = [];
    var specialWebcasts = this.props.webcastData.special_webcasts;
    var eventsWithWebcasts = this.props.webcastData.ongoing_events_w_webcasts;

    // First, deal with special webcasts
    for (var i = 0; i < specialWebcasts.length; i++) {
      webcasts.push({
        'key': specialWebcasts[i].key_name,
        'num': 1,
        'id': specialWebcasts[i].key_name + '-' + 1,
        'name': specialWebcasts[i].name,
        'type': specialWebcasts[i].type,
        'channel': specialWebcasts[i].channel
      });
    }

    // Now, process normal event webcasts
    for (var i = 0; i < eventsWithWebcasts.length; i++) {
      var event = eventsWithWebcasts[i];
      for (var j = 0; j < event.webcast.length; j++) {
        var webcast = event.webcast[i];
        var name = (event.short_name ? event.short_name : event.name);
        if (event.webcast.length > 1) {
          name += (' ' + (j + 1));
        }
        webcasts.push({
          'key': event.key,
          'num': (j + 1),
          'id': event.key + '-' + (j + 1),
          'name': name,
          'type': webcast.type,
          'channel': webcast.channel
        });
      }
    }

    this.setState({
      webcasts: webcasts
    });
  },
  componentWillUnmount: function() {
    this.serverRequest.abort();
  },
  render: function() {
    return (
      <div className="gameday container-full">
        <GamedayNavbar
          chatEnabled={this.state.chatEnabled}
          hashtagEnabled={this.state.hashtagEnabled}
          webcasts={this.state.webcasts}
          onChatToggle={this.handleChatToggle}
          onHashtagToggle={this.handleHashtagToggle}
          onWebcastAdd={this.handleWebcastAdd}
          onWebcastReset={this.handleWebcastReset} />
        <HashtagPanel enabled={this.state.hashtagEnabled} />
        <ChatPanel enabled={this.state.chatEnabled} />
        <VideoGrid
          webcasts={this.state.webcasts}
          displayedWebcasts={this.state.displayedWebcasts}
          rightPanelEnabled={this.state.chatEnabled}
          leftPanelEnabled={this.state.hashtagEnabled}
          onWebcastRemove={this.handleWebcastRemove} />
        <FollowingTeamsModal
          followingTeams={this.state.followingTeams}
          onFollowTeam={this.handleFollowTeam}
          onUnfollowTeam={this.handleUnfollowTeam} />
      </div>
    );
  },
  handleChatToggle: function() {
    this.setState({chatEnabled: !this.state.chatEnabled});
  },
  handleFollowTeam: function(team) {
    var newFollowingTeams = this.state.followingTeams.concat([team]);
    this.setState({followingTeams: newFollowingTeams})
  },
  handleHashtagToggle: function() {
    this.setState({hashtagEnabled: !this.state.hashtagEnabled});
  },
  handleWebcastAdd: function(webcast) {
    var displayedWebcasts = this.state.displayedWebcasts;
    var newDisplayedWebcasts = displayedWebcasts.concat([webcast.id]);
    this.setState({displayedWebcasts: newDisplayedWebcasts});
  },
  handleWebcastRemove: function(webcast) {
    var displayedWebcasts = this.state.displayedWebcasts;
    var newDisplayedWebcasts = displayedWebcasts.filter(function(id) {
      return id != webcast.id;
    });
    this.setState({displayedWebcasts: newDisplayedWebcasts});
  },
  handleUnfollowTeam: function(team) {
    var newFollowingTeams = this.state.followingTeams.filter(function(a) {
      return a != team
    });
    this.setState({followingTeams: newFollowingTeams});
  },
  handleWebcastReset: function() {
    this.setState({displayedWebcasts: []});
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
            <WebcastDropdown
              webcasts={this.props.webcasts}
              onWebcastAdd={this.props.onWebcastAdd}
              onWebcastReset={this.props.onWebcastReset} />
            <li>
              <BootstrapButton
                active={this.props.hashtagEnabled}
                handleClick={this.props.onHashtagToggle}>Hashtags</BootstrapButton>
            </li>
            <li>
              <BootstrapButton
                active={this.props.chatEnabled}
                handleClick={this.props.onChatToggle}>Chat</BootstrapButton>
            </li>
            <SettingsDropdown />
          </ul>
        </div>
      </nav>
    );
  }
});

var ChatPanel = React.createClass({
  render: function() {
    var classes = classNames({
      'hidden': !this.props.enabled,
      'pull-right': true,
      'sidebar': true,
    });
    return (
      <div className={classes}>
        <iframe frameBorder="0" scrolling="no" id="chat_embed" src="http://twitch.tv/chat/embed?channel=tbagameday&amp;popout_chat=true" height="100%" width="100%"></iframe>
      </div>
    );
  }
});

var HashtagPanel = React.createClass({
  componentDidMount: function() {
    !function(d,s,id){
      var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';
      if(!d.getElementById(id)){
        js=d.createElement(s);js.id=id;
        js.src=p+"://platform.twitter.com/widgets.js";
        fjs.parentNode.insertBefore(js,fjs);
      }
    }
    (document,"script","twitter-wjs");
    setTimeout(function(){$(".twitter-timeline").attr("height", "100%");}, 3000);
    // omg what a hack -gregmarra 20131226
  },
  componentDidUpdate: function() {
    $(".twitter-timeline").attr("height", "100%");
  },
  render: function() {
    var classes = classNames({
      'hidden': !this.props.enabled,
      'pull-left': true,
      'sidebar': true,
    });
    return (
      <div className={classes}>
        <div id="twitter-widget"><a className="twitter-timeline" href="https://twitter.com/search?q=%23omgrobots" data-widget-id="406597120632709121">Tweets about "#omgrobots"</a></div>
      </div>
    );
  }
});

var BootstrapButton = React.createClass({
  getDefaultProps: function() {
    return {
      a: '#'
    };
  },
  handleClick: function() {
    if (this.props.handleClick) {
      this.props.handleClick();
      return false;
    }
  },
  render: function() {
    var classes = classNames({
      'btn': true,
      'btn-default': true,
      'active': this.props.active,
    });
    return (
      <a className={classes} href={this.props.a} onClick={this.handleClick}>{this.props.children}</a>
    );
  }
});

/**
 * Responsible for rendering a number of webcasts in a grid-like
 * presentation.
 *
 * Should pr provided with both {webcasts} and {displayedWebcasts} as properties.
 * {webcasts} should be an array of webcast objects, and {displayedWebcasts}
 * should be an array of webcast ids.
 */
var VideoGrid = React.createClass({
  getWebcasts: function() {
    return _.filter(this.props.webcasts, function(webcast) {
      return _.indexOf(this.props.displayedWebcasts, webcast.id) >= 0;
    }, this);
  },
  renderLayoutZero: function(classes) {
    return (
      <div className={classes}>
        <div className="jumbotron">
          <h2>GameDay &mdash; Watch FIRST Webcasts</h2>
          <p>To get started, pick some webcasts from the top menu.</p>
        </div>
      </div>
    );
  },
  renderLayout: function(webcastCount, layoutNumber, classes) {
    classes += (' layout-' + layoutNumber);

    var videoCells = [];
    var webcasts = this.getWebcasts();
    for (var i = 0; i < webcastCount; i++) {
      var webcast = webcasts[i];
      videoCells.push(
        <VideoCell
          num={i}
          key={webcast.id}
          webcast={webcast}
          onWebcastRemove={this.props.onWebcastRemove}
          vidHeight="100%"
          vidWidth="100%" />
      );
    }

    return (
      <div className={classes}>
        {videoCells}
      </div>
    );
  },
  render: function() {
    var classes = classNames({
      'video-grid': true,
      'leave-left-margin': this.props.leftPanelEnabled,
      'leave-right-margin': this.props.rightPanelEnabled,
    });
    var layout;
    console.log(this.getWebcasts());
    console.log(this.getWebcasts().length);
    switch (this.getWebcasts().length) {
      case 0:
      return this.renderLayoutZero(classes);
      case 1:
      return this.renderLayout(1, 1, classes);
      case 2:
      return this.renderLayout(2, 2, classes);
      case 3:
      return this.renderLayout(3, 3, classes);
      case 4:
      return this.renderLayout(4, 4, classes);
    }
    return layout;
  },
});

var VideoCell = React.createClass({
  getInitialState: function() {
    return {
      showOverlay: false,
    };
  },
  onMouseEnter: function(event) {
    this.setState({"showOverlay": true})
  },
  onMouseLeave: function(event) {
    this.setState({"showOverlay": false})
  },
  render: function() {
    if (this.props.webcast) {
      var cellEmbed;
      switch (this.props.webcast.type) {
        case 'ustream':
        cellEmbed = <EmbedUstream
          webcast={this.props.webcast}
          vidHeight={this.props.vidHeight}
          vidWidth={this.props.vidWidth} />;
        break;
        case 'youtube':
        cellEmbed = <EmbedYoutube
          webcast={this.props.webcast}
          vidHeight={this.props.vidHeight}
          vidWidth={this.props.vidWidth} />;
        break;
        case 'twitch':
        cellEmbed = <EmbedTwitch
          webcast={this.props.webcast}
          vidHeight={this.props.vidHeight}
          vidWidth={this.props.vidWidth} />;
        break;
        default:
        cellEmbed = "";
        break;
      }

      var classes = 'video-cell video-' + this.props.num;

      return (
        <div className={classes}
          idName={this.props.webcast.id}
          onMouseEnter={this.onMouseEnter}
          onMouseLeave={this.onMouseLeave}>
          {cellEmbed}
          <VideoCellOverlay
            webcast={this.props.webcast}
            enabled={this.state.showOverlay}
            onWebcastRemove={this.props.onWebcastRemove} />
        </div>
      )
    } else {
      return <div className="video-cell" />
    }
  }
});

var VideoCellOverlay = React.createClass({
  onCloseClicked: function() {
    this.props.onWebcastRemove(this.props.webcast);
  },
  render: function() {
    var classes = classNames({
      'hidden': !this.props.enabled,
      'panel': true,
      'panel-default': true,
      'video-cell-overlay': true,
    });
    if (this.props.webcast) {
      return (
        <div className={classes}>
          <div className="panel-heading">
            <h3 className="panel-title">{this.props.webcast.name}</h3>
            <span className="button-close glyphicon glyphicon-remove" onClick={this.onCloseClicked}></span>
          </div>
        </div>
      )
    }
  }
});

var EmbedYoutube = React.createClass({
  render: function() {
    var src = "//www.youtube.com/embed/" + this.props.webcast.channel;
    return (
      <iframe
        width={this.props.vidWidth}
        height={this.props.vidHeight}
        src={src}
        frameBorder="0"
        allowFullScreen>
      </iframe>
    );
  }
});

var EmbedUstream = React.createClass({
  render: function() {
    var channel = this.props.webcast.channel;
    var src = `http://www.ustream.tv/embed/${channel}?html5ui=1`;
    return (
      <iframe
        width={this.props.vidWidth}
        height={this.props.vidHeight}
        src={src}
        scrolling="no"
        allowfullscreen
        webkitallowfullscreen
        frameborder="0"
        style={{border: "0 none transparent"}}></iframe>
    );
  }
});

var EmbedTwitch = React.createClass({
  render: function() {
    var channel = this.props.webcast.channel;
    var src = `http://www.twitch.tv/widgets/live_embed_player.swf?channel=${channel}`;
    var flashvars = `hostname=www.twitch.tv&channel=${channel}&auto_play=true&start_volume=25&enable_javascript=true`;
    return (
      <object
        type='application/x-shockwave-flash'
        height='100%'
        width='100%'
        id='live_embed_player_flash'
        data={src}
        bgcolor='#000000'>
        <param name='allowFullScreen' value='true' />
        <param name='allowScriptAccess' value='always' />
        <param name='allowNetworking' value='all' />
        <param
          name='movie'
          value='http://www.twitch.tv/widgets/live_embed_player.swf' />
        <param
          name='flashvars'
          value={flashvars} />
        <param name='wmode' value='transparent' />
      </object>
    );
  }
});

var WebcastDropdown = React.createClass({
  render: function() {
    var webcastListItems = [];
    for (var i = 0; i < this.props.webcasts.length; i++) {
      var webcast = this.props.webcasts[i];
      webcastListItems.push(
        <WebcastListItem
          key={webcast.id}
          webcast={webcast}
          onWebcastAdd={this.props.onWebcastAdd} />
      );
    }
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Add Webcasts <b className="caret"></b></a>
        <ul className="dropdown-menu">
          {webcastListItems}
          <li className="divider"></li>
          <BootstrapNavDropdownListItem handleClick={this.props.onWebcastReset}>Reset Webcasts</BootstrapNavDropdownListItem>
        </ul>
      </li>
    );
  }
})

var SettingsDropdown = React.createClass({
  render: function() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown"><span className="glyphicon glyphicon-cog"></span></a>
        <ul className="dropdown-menu">
          <BootstrapNavDropdownListItem
            data_toggle="modal"
            data_target="#followingTeamsModal">Follow Teams</BootstrapNavDropdownListItem>
          <li className="divider"></li>
          <BootstrapNavDropdownListItem>Debug Menu</BootstrapNavDropdownListItem>
          <BootstrapNavDropdownListItem>TODO Show Beeper</BootstrapNavDropdownListItem>
        </ul>
      </li>
    );
  }
})

var WebcastListItem = React.createClass({
  handleClick: function() {
    this.props.onWebcastAdd(this.props.webcast);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
})

var BootstrapNavDropdownListItem = React.createClass({
  getDefaultProps: function() {
    return {
      a: '#'
    };
  },
  handleClick: function() {
    if (this.props.handleClick) {
      this.props.handleClick();
      return false;
    }
  },
  render: function() {
    return (
      <li data-toggle={this.props.data_toggle} data-target={this.props.data_target}><a href={this.props.a} onClick={this.handleClick}>{this.props.children}</a></li>
    )
  },
})

var FollowingTeamListItem = React.createClass({
  unfollowTeam: function() {
    this.props.onUnfollowTeam(this.props.team)
  },
  render: function() {
    return (
      <li>
        {this.props.team}
        <a href="#" onClick={this.unfollowTeam}>&times;</a>
      </li>
    );
  }
})

var FollowingTeamsModal = React.createClass({
  followTeam: function() {
    this.props.onFollowTeam(177)
  },
  render: function() {
    var followingTeamListItems = [];
    for (var index in this.props.followingTeams) {
      followingTeamListItems.push(
        <FollowingTeamListItem
          key={this.props.followingTeams[index]}
          team={this.props.followingTeams[index]}
          onUnfollowTeam={this.props.onUnfollowTeam} />
      );
    };
    return (
      <div className="modal fade" id="followingTeamsModal" tabindex="-1" role="dialog" aria-labelledby="#followingTeamsModal" aria-hidden="true">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <button type="button" className="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span className="sr-only">Close</span></button>
              <h4 className="modal-title" id="followingTeamsModalLabel">Following Teams</h4>
            </div>
            <div className="modal-body">
              <p>You can follow teams to get alerts about them.</p>
              <div className="input-group">
                <input className="form-control" type="text" placeholder="Team Number"></input>
                <span className="input-group-btn">
                  <a onClick={this.followTeam} href="#" className="btn btn-primary"><span className="glyphicon glyphicon-plus-sign"></span></a>
                </span>
              </div>
              <hr></hr>
              <h4>Following</h4>
              <ul>{followingTeamListItems}</ul>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-primary" data-dismiss="modal">Done</button>
            </div>
          </div>
        </div>
      </div>
    );
  }
})


// [{'webcasts': [{u'channel': u'6540154', u'type': u'ustream'}], 'event_name': u'Present Test Event', 'event_key': u'2014testpresent'}]

var webcastData = $.parseJSON($("#webcasts_json").text().replace(/u'/g,/u'/g,/u'/g,/u'/g,/u'/g,/u'/g,/u'/g,/u'/g,'\'').replace(/'/g,/'/g,/'/g,/'/g,/'/g,/'/g,/'/g,/'/g,'"'));

ReactDOM.render(
  <GamedayFrame webcastData={webcastData} pollInterval={20000} />,
  document.getElementById('content')
);
