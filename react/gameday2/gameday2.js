var React = require('react');
var ReactDOM = require('react-dom');
var classNames = require('classnames');
var _ = require('underscore');

import GamedayNavbar from './components/GamedayNavbar';
import VideoGrid from './components/VideoGrid';

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
