import React from 'react'
import GamedayNavbarContainer from '../containers/GamedayNavbarContainer'
import MainContentContainer from '../containers/MainContentContainer'
import ChatSidebarContainer from '../containers/ChatSidebarContainer'
import HashtagSidebarContainer from '../containers/HashtagSidebarContainer'

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
    const newFollowingTeams = this.state.followingTeams.filter(a => a !== team)
    this.setState({ followingTeams: newFollowingTeams })
  },
  render() {
    return (
      <div className="gameday container-full">
        <GamedayNavbarContainer />
        <HashtagSidebarContainer />
        <ChatSidebarContainer />
        <MainContentContainer />
      </div>
    )
  },
})

export default GamedayFrame
