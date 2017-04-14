import React from 'react'
import AppBarContainer from '../containers/AppBarContainer'
import MainContentContainer from '../containers/MainContentContainer'
import ChatSidebarContainer from '../containers/ChatSidebarContainer'
import HashtagSidebarContainer from '../containers/HashtagSidebarContainer'
import CastReceiverContainer from '../containers/CastReceiverContainer'

const GamedayFrame = () => (
  <div className="gameday container-full">
    <AppBarContainer />
    <HashtagSidebarContainer />
    <ChatSidebarContainer />
    <MainContentContainer />
    <CastReceiverContainer />
  </div>
)

export default GamedayFrame
