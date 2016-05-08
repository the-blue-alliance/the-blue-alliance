import { connect } from 'react-redux'
import VideoGrid from '../components/VideoGrid'
import { addWebcastAtLocation, removeWebcast, setLayout } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => {
  return {
    webcasts: getWebcastIdsInDisplayOrder(state),
    webcastsById: state.webcastsById,
    displayedWebcasts: state.displayedWebcasts,
    hashtagSidebarVisible: state.visibility.hashtagSidebar,
    chatSidebarVisible: state.visibility.chatSidebar,
    layoutId: state.layout.layoutId,
    layoutSet: state.layout.layoutSet
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    addWebcastAtLocation: (webcastId, location) => dispatch(addWebcastAtLocation(webcastId, location)),
    setLayout: (layoutId) => dispatch(setLayout(layoutId))
  }
}

const VideoGridContainer = connect(mapStateToProps, mapDispatchToProps)(VideoGrid)

export default VideoGridContainer
