import React, { Component } from 'react'
import PropTypes from 'prop-types'
import TeamItem from './TeamItem'

const TeamList = (props) => (
  <div>
    {props.teams.length > 0 &&
    <p>
      {props.teams.length} teams attending
    </p>
    }
    <ul>
      {props.teams.map((team) =>
        <TeamItem
          key={team.key}
          team_number={team.team_number}
          nickname={team.nickname}
        />
      )}
    </ul>
  </div>
)

TeamList.propTypes = {
  teams: PropTypes.array.isRequired,
}

export default TeamList
