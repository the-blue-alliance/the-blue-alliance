import React from 'react'
import AppBarContainer from '../containers/AppBarContainer'
import MainContentContainer from '../containers/MainContentContainer'
import ChatSidebarContainer from '../containers/ChatSidebarContainer'
import HashtagSidebarContainer from '../containers/HashtagSidebarContainer'

const GamedayFrame = () => (
  <div className="gameday container-full">
    <AppBarContainer />
    <HashtagSidebarContainer />
    <ChatSidebarContainer />
    <MainContentContainer />
  </div>
)

export default GamedayFrame
