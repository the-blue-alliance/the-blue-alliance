import React, { PropTypes } from 'react'

function getStyles(props, state) {
  let backgroundColor
  if (props.enabled) {
    if (state.hovered) {
      backgroundColor = '#aaaaaa'
    } else {
      backgroundColor = '#cccccc'
    }
  } else {
    backgroundColor = '#555555'
  }

  const style = {
    padding: '4px',
    backgroundClip: 'content-box',
    backgroundColor,
    cursor: props.enabled ? 'pointer' : null,
  }

  return Object.assign({}, style, props.style)
}

export default class SwapPositionPreviewCell extends React.Component {
  static propTypes = {
    style: PropTypes.object.isRequired,
    enabled: PropTypes.bool.isRequired,
    onClick: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props)

    this.state = {
      hovered: false,
    }
  }

  onMouseOver() {
    this.setState({
      hovered: true,
    })
  }

  onMouseOut() {
    this.setState({
      hovered: false,
    })
  }

  onClick() {
    if (this.props.onClick) {
      this.props.onClick()
    }
  }

  render() {
    const styles = getStyles(this.props, this.state)

    return (
      <div
        style={styles}
        onMouseOver={() => this.onMouseOver()}
        onMouseOut={() => this.onMouseOut()}
        onClick={() => this.onClick()}
      />
    )
  }
}
