var React = require('react');
var ReactDOM = require('react-dom');
var classNames = require('classnames');
var _ = require('underscore');

import GamedayNavbar from './components/GamedayNavbar';
import VideoGrid from './components/VideoGrid';
import ChatPanel from './components/ChatPanel';
import HashtagPanel from './components/HashtagPanel';
import FollowingTeamModal from './components/FollowingTeamModal';

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

// [{'webcasts': [{u'channel': u'6540154', u'type': u'ustream'}], 'event_name': u'Present Test Event', 'event_key': u'2014testpresent'}]

var webcastData = $.parseJSON($("#webcasts_json").text().replace(/u'/g,'\'').replace(/'/g,'"'));

ReactDOM.render(
  <GamedayFrame webcastData={webcastData} pollInterval={20000} />,
  document.getElementById('content')
);
