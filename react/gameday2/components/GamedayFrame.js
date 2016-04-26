import React from 'react';
import GamedayNavbarContainer from '../containers/GamedayNavbarContainer';
import VideoGrid from './VideoGrid';
import ChatPanelContainer from '../containers/ChatPanelContainer';
import HashtagPanelContainer from '../containers/HashtagPanelContainer';
import FollowingTeamsModal from './FollowingTeamsModal';

var GamedayFrame = React.createClass({
  getInitialState: function() {
    return {
      webcasts: [],
      webcastsById: {},
      displayedWebcasts: [],
      followingTeams: [177,230]
    };
  },
  render: function() {
    return (
      <div className="gameday container-full">
        <GamedayNavbarContainer
          onWebcastAdd={this.handleWebcastAdd}
          onWebcastReset={this.handleWebcastReset} />
        <HashtagPanelContainer />
        <ChatPanelContainer />
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
  handleFollowTeam: function(team) {
    var newFollowingTeams = this.state.followingTeams.concat([team]);
    this.setState({followingTeams: newFollowingTeams})
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

export default GamedayFrame;
