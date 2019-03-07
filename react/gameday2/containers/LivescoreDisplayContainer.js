import { connect } from 'react-redux'
import LivescoreDisplay2019 from '../components/LivescoreDisplay2019'
import { getEventMatches, getCurrentMatchState } from '../selectors'

const mapStateToProps = (state, props) => ({
  matches: getEventMatches(state, props),
  matchState: getCurrentMatchState(state, props),
})

export default connect(mapStateToProps)(LivescoreDisplay2019)
