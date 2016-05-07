import { connect } from 'react-redux'
import HashtagSidebar from '../components/hashtagSidebar'

const mapStateToProps = (state) => {
  return {
    enabled: state.visibility.hashtagSidebar
  }
}

const HashtagSidebarContainer = connect(mapStateToProps, null)(HashtagSidebar)

export default HashtagSidebarContainer
