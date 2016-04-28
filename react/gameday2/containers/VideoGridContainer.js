import { connect } from 'react-redux'
import VideoGrid from '../components/VideoGrid'
import { removeWebcast } from '../actions'

const mapStateToProps = (state) => {
  return {
    webcasts: state.webcasts,
    webcastsById: state.webcastsById,
    displayedWebcasts: state.displayedWebcasts,
    hashtagPanelVisible: state.hashtagPanelVisible,
    chatPanelVisible: state.chatPanelVisible,
    layoutId: state.layout.layoutId,
    layoutSet: state.layout.layoutSet
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    removeWebcast: (id) => dispatch(removeWebcast(id)),
  }
}

const VideoGridContainer = connect(mapStateToProps, mapDispatchToProps)(VideoGrid)

export default VideoGridContainer
