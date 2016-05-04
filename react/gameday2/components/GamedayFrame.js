import React from 'react';
import GamedayNavbarContainer from '../containers/GamedayNavbarContainer';
import VideoGridContainer from '../containers/VideoGridContainer';
import ChatPanelContainer from '../containers/ChatPanelContainer';
import HashtagPanelContainer from '../containers/HashtagPanelContainer';
import FollowingTeamsModal from './FollowingTeamsModal';

var GamedayFrame = React.createClass({
  getInitialState: function() {
    return {
      followingTeams: [177,230]
    };
  },
  render: function() {
    return (
      <div className="gameday container-full">
        <GamedayNavbarContainer />
        <HashtagPanelContainer />
        <ChatPanelContainer />
        <VideoGridContainer />
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
  handleUnfollowTeam: function(team) {
    var newFollowingTeams = this.state.followingTeams.filter(function(a) {
      return a != team
    });
    this.setState({followingTeams: newFollowingTeams});
  }
});

export default GamedayFrame;
