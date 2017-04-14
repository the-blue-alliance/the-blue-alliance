import { connect } from 'react-redux'
import CastReceiver from '../components/CastReceiver'
import * as actions from '../actions'

const mapStateToProps = (state) => ({

})

const mapDispatchToProps = (dispatch) => ({
  setLayout: (layoutId) => dispatch(actions.setLayout(layoutId)),
  addWebcastAtPosition: (webcastId, position) => dispatch(actions.addWebcastAtPosition(webcastId, position)),
})

export default connect(mapStateToProps, mapDispatchToProps)(CastReceiver)