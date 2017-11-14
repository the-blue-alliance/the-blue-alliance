import PropTypes from 'prop-types'
import WEBCAST_SHAPE from './ApiWebcast'

const EVENT_SHAPE = {
  key: PropTypes.string.isRequired,
  playoff_type: PropTypes.int,
  first_event_code: PropTypes.string,
  webcasts: PropTypes.arrayOf(PropTypes.shape(WEBCAST_SHAPE)),
  remap_teams: PropTypes.object,
}

export default EVENT_SHAPE
