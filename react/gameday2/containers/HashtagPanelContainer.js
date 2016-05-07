import { connect } from 'react-redux'
import HashtagPanel from '../components/HashtagPanel'

const mapStateToProps = (state) => {
  return {
    enabled: state.visibility.hashtagPanel
  }
}

const HashtagPanelContainer = connect(mapStateToProps, null)(HashtagPanel)

export default HashtagPanelContainer
