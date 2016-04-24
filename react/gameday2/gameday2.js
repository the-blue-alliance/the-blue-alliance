var React = require('react');
var ReactDOM = require('react-dom');
var classNames = require('classnames');
var _ = require('underscore');

import GamedayNavbar from './components/GamedayNavbar';

var GamedayFrame = React.createClass({
  getInitialState: function() {
    return {
      webcasts: [],
      webcastsById: {},
      displayedWebcasts: [],
      hashtagEnabled: true,
      chatEnabled: false,
      followingTeams: [177,230]
    };
  },
  componentWillMount: function() {
    // Process webcast data
    // Special and event webcasts are normalized into objects with 6 attributes:
    // key, num, id, name, type, and channel
    var webcasts = [];
    var webcastsById = {};
    var specialWebcasts = this.props.webcastData.special_webcasts;
    var eventsWithWebcasts = this.props.webcastData.ongoing_events_w_webcasts;

    // First, deal with special webcasts
    for (let webcast of specialWebcasts) {
      const id = webcast.key_name + 0;
      webcasts.push(id);
      webcastsById[id] = {
        'key': webcast.key_name,
        'num': 0,
        'id': id,
        'name': webcast.name,
        'type': webcast.type,
        'channel': webcast.channel
      };
    }

    // Now, process normal event webcasts
    for (let event of eventsWithWebcasts) {
      var webcastNum = 0;
      for (let webcast of event.webcast) {
        var name = (event.short_name ? event.short_name : event.name);
        if (event.webcast.length > 1) {
          name += (' ' + (webcastNum + 1));
        }
        const id = event.key + '-' + webcastNum;
        webcasts.push(id);
        webcastsById[id] = {
          'key': event.key,
          'num': webcastNum,
          'id': id,
          'name': name,
          'type': webcast.type,
          'channel': webcast.channel
        };
        webcastNum++;
      }
    }

    this.setState({
      webcasts: webcasts,
      webcastsById: webcastsById
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
          webcastsById={this.state.webcastsById}
          onChatToggle={this.handleChatToggle}
          onHashtagToggle={this.handleHashtagToggle}
          onWebcastAdd={this.handleWebcastAdd}
          onWebcastReset={this.handleWebcastReset} />
        <HashtagPanel enabled={this.state.hashtagEnabled} />
        <ChatPanel enabled={this.state.chatEnabled} />
        <VideoGrid
          webcasts={this.state.webcasts}
          webcastsById={this.state.webcastsById}
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

/**
 * Responsible for rendering a number of webcasts in a grid-like
 * presentation.
 *
 * Should pr provided with both {webcasts} and {displayedWebcasts} as properties.
 * {webcasts} should be an array of webcast objects, and {displayedWebcasts}
 * should be an array of webcast ids.
 */
var VideoGrid = React.createClass({
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
    for (var i = 0; i < webcastCount; i++) {
      var webcast = null, id = 'video-' + i;
      if (i < this.props.displayedWebcasts.length) {
        webcast = this.props.webcastsById[this.props.displayedWebcasts[i]];
        id = webcast.id;
      }
      videoCells.push(
        <VideoCell
          num={i}
          key={id}
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
    switch (this.props.displayedWebcasts.length) {
      case 0:
      layout = this.renderLayoutZero(classes);
      break;
      case 1:
      layout = this.renderLayout(1, 1, classes);
      break;
      case 2:
      layout = this.renderLayout(2, 2, classes);
      break;
      case 3:
      layout = this.renderLayout(3, 3, classes);
      break;
      case 4:
      layout = this.renderLayout(4, 4, classes);
      break;
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
    var classes = 'video-cell video-' + this.props.num;

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
      return <div className={classes} />
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

var webcastData = $.parseJSON($("#webcasts_json").text().replace(/u'/g,'\'').replace(/'/g,'"'));

ReactDOM.render(
  <GamedayFrame webcastData={webcastData} pollInterval={20000} />,
  document.getElementById('content')
);
