import React from 'react'
import PropTypes from 'prop-types'

const TeamItem = (props) => (
  <p>Team {props.team_number} - <a href={`/team/${props.team_number}`}>{props.nickname}</a></p>
)

TeamItem.propTypes = {
  team_number: PropTypes.number.isRequired,
  nickname: PropTypes.string.isRequired,
}

export default TeamItem
