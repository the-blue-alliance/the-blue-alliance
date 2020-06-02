import { connect } from 'react-redux'
import LivescoreDisplay from '../components/LivescoreDisplay'
import { getEventMatches, getCurrentMatchState } from '../selectors'

const mapStateToProps = (state, props) => ({
  matches: getEventMatches(state, props),
  matchState: getCurrentMatchState(state, props),
})

export default connect(mapStateToProps)(LivescoreDisplay)
