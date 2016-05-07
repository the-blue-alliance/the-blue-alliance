import { connect } from 'react-redux'
import GamedayTicker from '../components/ticker/GamedayTicker'

const mapStateToProps = (state) => {
  return {
    enabled: state.visibility.tickerPanel
  }
}

const HashtagPanelContainer = connect(mapStateToProps, null)(GamedayTicker)

export default TickerPanelContainer
