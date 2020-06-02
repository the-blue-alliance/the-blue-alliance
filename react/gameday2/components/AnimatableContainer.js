import React, { PropTypes } from 'react'

export default class AnimatableContainer extends React.Component {
  static propTypes = {
    beginStyle: PropTypes.object.isRequired,
    endStyle: PropTypes.object.isRequired,
    style: PropTypes.object,
    children: PropTypes.node,
  }

  constructor(props) {
    super(props)

    this.state = {
      style: props.beginStyle,
    }
  }

  componentWillUnmount() {
    clearTimeout(this.enterTimeout)
    clearTimeout(this.leaveTimeout)
  }

  componentWillEnter(callback) {
    this.componentWillAppear(callback)
  }

  componentWillAppear(callback) {
    // Timeout needed so that the component can render with the original styles
    // before we apply the ones to transition to
    setTimeout(() => this.setState({
      style: this.props.endStyle,
    }), 0)

    this.enterTimeout = setTimeout(callback, 300)
  }

  componentWillLeave(callback) {
    this.setState({
      style: this.props.beginStyle,
    })

    this.leaveTimeout = setTimeout(callback, 300)
  }

  render() {
    /* eslint-disable no-unused-vars */
    // beginStyle and endStyle are unused, but we exclude them from ...other so
    // they don't get passed as props to our div
    const {
      style,
      children,
      beginStyle,
      endStyle,
      ...other
    } = this.props

    return (
      <div {...other} style={Object.assign({}, style, this.state.style)}>
        {children}
      </div>
    )
  }
}
