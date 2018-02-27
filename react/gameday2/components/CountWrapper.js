import React from 'react'
import PropTypes from 'prop-types'
import CountUp from 'react-countup'

class CountWrapper extends React.PureComponent {
  constructor(props) {
    super(props)
    this.state = {
      start: props.number,
      end: props.number,
    }
  }

  componentWillUpdate(nextProps) {
    this.setState({
      start: this.state.end,
      end: nextProps.number,
    })
  }

  render() {
    return <CountUp start={this.state.start} end={this.state.end} duration={1} />
  }
}

CountWrapper.propTypes = {
  number: PropTypes.number.isRequired,
}

export default CountWrapper
