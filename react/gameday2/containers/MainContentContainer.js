import { connect } from 'react-redux'
import MainContent from '../components/MainContent'
import { setLayout } from '../actions'
import { getWebcastIds } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIds(state),
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
  layoutSet: state.videoGrid.layoutSet,
})


const mapDispatchToProps = (dispatch) => ({
  setLayout: (layoutId) => dispatch(setLayout(layoutId)),
})

export default connect(mapStateToProps, mapDispatchToProps)(MainContent)
