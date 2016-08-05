import { connect } from 'react-redux'
import MainContent from '../components/MainContent'
import { setLayout } from '../actions'
import { getWebcastIds } from '../selectors'

const mapStateToProps = (state) => {
  return {
    webcasts: getWebcastIds(state),
    hashtagSidebarVisible: state.visibility.hashtagSidebar,
    chatSidebarVisible: state.visibility.chatSidebar,
    layoutSet: state.layout.layoutSet
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    setLayout: (layoutId) => dispatch(setLayout(layoutId))
  }
}

const MainContentContainer = connect(mapStateToProps, mapDispatchToProps)(MainContent)

export default MainContentContainer
