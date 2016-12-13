import React from 'react'
import GamedayNavbarContainerMaterial from '../containers/GamedayNavbarContainerMaterial'
import MainContentContainer from '../containers/MainContentContainer'
import ChatSidebarContainer from '../containers/ChatSidebarContainer'
import HashtagSidebarContainer from '../containers/HashtagSidebarContainer'
import FollowingTeamsModal from './FollowingTeamsModal'

const GamedayFrame = React.createClass({
  getInitialState() {
    return {
      followingTeams: [177, 230],
    }
  },
  handleFollowTeam(team) {
    const newFollowingTeams = this.state.followingTeams.concat([team])
    this.setState({ followingTeams: newFollowingTeams })
  },
  handleUnfollowTeam(team) {
    const newFollowingTeams = this.state.followingTeams.filter((a) => a !== team)
    this.setState({ followingTeams: newFollowingTeams })
  },
  render() {
    return (
      <div className="gameday container-full">
        <GamedayNavbarContainerMaterial />
        <HashtagSidebarContainer />
        <ChatSidebarContainer />
        <MainContentContainer />
        <FollowingTeamsModal
          followingTeams={this.state.followingTeams}
          onFollowTeam={this.handleFollowTeam}
          onUnfollowTeam={this.handleUnfollowTeam}
        />
      </div>
    )
  },
})

export default GamedayFrame
