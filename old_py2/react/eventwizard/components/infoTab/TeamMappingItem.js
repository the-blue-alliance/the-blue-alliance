import React, { Component } from 'react'
import PropTypes from 'prop-types'

class TeamMappingItem extends Component {
  constructor(props) {
    super(props)
    this.onRemoveClick = this.onRemoveClick.bind(this)
  }

  onRemoveClick() {
    this.props.removeTeamMap(this.props.fromTeamKey)
  }

  render() {
    return (
      <p>{this.props.fromTeamKey.substr(3)} <span className="glyphicon glyphicon-arrow-right" aria-hidden="true" /> {this.props.toTeamKey.substr(3)} &nbsp;
        <button
          className="btn btn-danger"
          onClick={this.onRemoveClick}
        >
          Remove
        </button>
      </p>
    )
  }
}

TeamMappingItem.propTypes = {
  fromTeamKey: PropTypes.string.isRequired,
  toTeamKey: PropTypes.string.isRequired,
  removeTeamMap: PropTypes.func.isRequired,
}

export default TeamMappingItem
