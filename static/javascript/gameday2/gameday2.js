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
      chatEnabled: false,
      displayedEvents: [],
      events: [],
      followingTeams: [177,230],
      hashtagEnabled: false,
    };
  },
  componentWillMount: function() {
    this.setState({events: this.props.events});
    this.setInitialState();
  },
  setInitialState: function() {
    this.setState({
      displayedEvents: this.props.events,
      hashtagEnabled: true,
    });
  },
  render: function() {
    return (
      <div className="gameday container-full">
        <GamedayNavbar 
          chatEnabled={this.state.chatEnabled}
          hashtagEnabled={this.state.hashtagEnabled}
          events={this.state.events}
          onChatToggle={this.handleChatToggle}
          onHashtagToggle={this.handleHashtagToggle}
          onWebcastAdd={this.handleWebcastAdd}
          onWebcastReset={this.handleWebcastReset} />
        <HashtagPanel enabled={this.state.hashtagEnabled} />
        <VideoGrid 
          events={this.state.displayedEvents}
          rightPanelEnabled={this.state.chatEnabled}
          leftPanelEnabled={this.state.hashtagEnabled} />
        <ChatPanel enabled={this.state.chatEnabled} />
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
    this.setState({followingTeams: this.state.followingTeams.push(team)})
  },
  handleHashtagToggle: function() {
    this.setState({hashtagEnabled: !this.state.hashtagEnabled});
  },
  handleWebcastAdd: function(eventModel) {
    var displayedEvents = this.state.displayedEvents;
    var newDisplayedEvents = displayedEvents.concat([eventModel]);
    this.setState({displayedEvents: newDisplayedEvents});
  },
  handleUnfollowTeam: function(team) {
    var newFollowingTeams = this.state.followingTeams.filter(function(a) {
      return a != team
    });
    this.setState({followingTeams: newFollowingTeams});
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
            <WebcastDropdown
              events={this.props.events}
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
    var cx = React.addons.classSet;
    var classes = cx({
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
    var cx = React.addons.classSet;
    var classes = cx({
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
    var cx = React.addons.classSet;
    var classes = cx({
      'btn': true,
      'btn-default': true,
      'active': this.props.active,
    });
    return (
      <a className={classes} href={this.props.a} onClick={this.handleClick}>{this.props.children}</a>
    );
  }
});

var VideoGrid = React.createClass({
  render: function() {
    var cx = React.addons.classSet;
    var classes = cx({
      'videoGrid': true,
      'leaveLeftMargin': this.props.leftPanelEnabled,
      'leaveRightMargin': this.props.rightPanelEnabled,
    });
    switch (this.props.events.length) {
      case 0:
        var layout = <VideoCellLayoutZero />
        break;
      case 1:
        var layout = <VideoCellLayoutOne events={this.props.events} />
        break;
      case 2:
        var layout = <VideoCellLayoutTwo events={this.props.events} />
        break;
      case 3:
        var layout = <VideoCellLayoutThree events={this.props.events} />
        break;
    }
    return (
      <div className={classes}>
        {layout}
      </div>
    );
  },
});

var VideoCellLayoutZero = React.createClass({
  render: function() {
    return (
        <div className="row">
          <div className="col-md-12">
            <div className="panel panel-default">
              <div className="panel-body">
                <div className="jumbotron">
                  <h2>GameDay &mdash; Watch FIRST Webcasts</h2>
                  <p>To get started, pick some webcasts from the top menu.</p>
                </div>
              </div>
            </div>   
          </div>
        </div>
      );
  }
});

var VideoCellLayoutOne = React.createClass({
  render: function() {
    if (this.props.events) {
      var eventModel = this.props.events[0];
    } else {
      var eventModel = null;
    }
    return (
        <div className="row">
          <div className="col-md-12">      
            <VideoCell
              eventModel={eventModel}
              vidHeight="100%"
              vidWidth="100%" />
          </div>
        </div>
      );
  }
});

var VideoCellLayoutTwo = React.createClass({
  render: function() {
    return (
        <div className="row">
          <div className="col-md-6">
            <VideoCell
              eventModel={this.props.events[0]}
              vidHeight="100%"
              vidWidth="100%" />
          </div>
          <div className="col-md-6">
            <VideoCell
              eventModel={this.props.events[1]}
              vidHeight="100%"
              vidWidth="100%" />
          </div>
        </div>
      );
  }
});

var VideoCellLayoutThree = React.createClass({
  render: function() {
    return (
        <div className="row">
          <div className="col-md-6">
            <VideoCell
              eventModel={this.props.events[0]}
              vidHeight="100%"
              vidWidth="100%" />
          </div>
          <div className="col-md-6">
            <div className="row">
              <div className="col-md-12">
                <VideoCell
                  eventModel={this.props.events[1]}
                  vidHeight="50%"
                  vidWidth="100%" />
              </div>
            </div>
            <div className="row">
              <div className="col-md-12">
                <VideoCell
                  eventModel={this.props.events[2]}
                  vidHeight="50%"
                  vidWidth="100%" />
              </div>
            </div>
          </div>
        </div>
      );
  }
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
    if (this.props.eventModel) {
      var id = this.props.eventModel.name + "-1";
      switch (this.props.eventModel.webcast[0].type) {
        case "ustream":
          cellEmbed = <EmbedUstream
            eventModel={this.props.eventModel}
            vidHeight={this.props.vidHeight}
            vidWidth={this.props.vidWidth} />;
          break;
        case "youtube":
          cellEmbed = <EmbedYoutube
            eventModel={this.props.eventModel}
            vidHeight={this.props.vidHeight}
            vidWidth={this.props.vidWidth} />;
          break;
        default:
          cellEmbed = "";
          break;
      }
      return (
        <div className="videoCell" 
          idName={id}
          onMouseEnter={this.onMouseEnter}
          onMouseLeave={this.onMouseLeave}>
          
          <VideoCellOverlay eventModel={this.props.eventModel} enabled={this.state.showOverlay} />
          {cellEmbed}
        </div>
      )
    } else {
      return <div className="videoCell" />
    }
  }
});

var VideoCellOverlay = React.createClass({
  render: function() {
    var cx = React.addons.classSet;
    var classes = cx({
      'hidden': !this.props.enabled,
      'panel': true,
      'panel-default': true,
      'videoCellOverlay': true,
    });
    if (this.props.eventModel) {
      return (
        <div className={classes}>
          <div className="panel-heading">
            <h3 className="panel-title">{this.props.eventModel.name}</h3>
          </div>
          <div className="panel-body"></div>
        </div>
      )
    }
  }
})

var EmbedYoutube = React.createClass({
  render: function() {
    var src = "//www.youtube.com/embed/" + this.props.eventModel.webcast[0].channel;
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
})

var EmbedUstream = React.createClass({
  render: function() {
    var src = "http://www.ustream.tv/flash/live/" + this.props.eventModel.webcast[0].channel;
    return (
      <object
        id='utv_o_322919'
        height={this.props.vidHeight}
        width={this.props.vidWidth}
        classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'>
        <param value={src} name='movie' />
        <param value='true' name='allowFullScreen' />
        <param value='always' name='allowScriptAccess' />
        <param value='transparent' name='wmode' />
        <param value='viewcount=true&autoplay=true&brand=embed&' name='flashvars' />
        <embed
          name='utv_e_218829'
          id='utv_e_209572'
          flashvars='viewcount=true&autoplay=true&brand=embed'
          height={this.props.vidHeight}
          width={this.props.vidWidth}
          allowFullScreen='true'
          allowScriptAccess='always'
          wmode='transparent'
          src={src}
          type='application/x-shockwave-flash' />
      </object>
      )
  }
})

var WebcastDropdown = React.createClass({
  render: function() {
    var webcastListItems = [];
    for (var index in this.props.events) {
      webcastListItems.push(<WebcastListItem eventModel={this.props.events[index]} onWebcastAdd={this.props.onWebcastAdd} />)
    };
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
    this.props.onWebcastAdd(this.props.eventModel);
  },
  render: function() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.eventModel.event_name}</BootstrapNavDropdownListItem>
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
      <li data-toggle={this.props.data_toggle} data-target={this.props.data_target}><a href={this.props.a} onClick={this.handleClick}>{this.props.children}</a></li>
    )
  },
})

var FollowingTeamListItems = React.createClass({
  unfollowTeam: function() {
    this.props.onUnfollowTeam(this.props.team)
  },
  render: function() {
    return (
      <li>
        {this.props.team} 
        <a href="#" onClick={this.unfollowTeam}>x</a>
      </li>
    );
  }
})

var FollowingTeamsModal = React.createClass({
  render: function() {
    var followingTeamListItems = [];
    for (var index in this.props.followingTeams) {
      followingTeamListItems.push(
        <FollowingTeamListItems
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

var events_with_webcasts = $.parseJSON($("#events_with_webcasts").text().replace(/u'/g,'\'').replace(/'/g,'"'));

React.renderComponent(
  <GamedayFrame events={events_with_webcasts} pollInterval={20000} />,
  document.getElementById('content')
);