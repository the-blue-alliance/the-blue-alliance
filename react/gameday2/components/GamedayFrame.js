import React from 'react'
import GamedayNavbarContainer from '../containers/GamedayNavbarContainer'
import MainContentContainer from '../containers/MainContentContainer'
import VideoGridContainer from '../containers/VideoGridContainer'
import ChatSidebarContainer from '../containers/ChatSidebarContainer'
import HashtagSidebarContainer from '../containers/HashtagSidebarContainer'
import FollowingTeamsModal from './FollowingTeamsModal'

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
        <HashtagSidebarContainer />
        <ChatSidebarContainer />
        <MainContentContainer />
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
