import React from 'react'
import GamedayNavbarContainer from '../containers/GamedayNavbarContainer'
import MainContentContainer from '../containers/MainContentContainer'
import ChatSidebarContainer from '../containers/ChatSidebarContainer'
import HashtagSidebarContainer from '../containers/HashtagSidebarContainer'

const GamedayFrame = () => (
  <div className="gameday container-full">
    <GamedayNavbarContainer />
    <HashtagSidebarContainer />
    <ChatSidebarContainer />
    <MainContentContainer />
  </div>
)

export default GamedayFrame
