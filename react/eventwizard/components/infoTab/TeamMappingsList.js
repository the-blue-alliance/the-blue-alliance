import React from 'react'
import PropTypes from 'prop-types'
import TeamMappingItem from './TeamMappingItem'


const TeamMappingsList = (props) => (
  <div>
    {Object.keys(props.teamMappings).length > 0 &&
    <p>
      {Object.keys(props.teamMappings).length} team mappings found
    </p>
    }
    <ul>
      {Object.entries(props.teamMappings).map((teamKeys) =>
        <li key={teamKeys[0]}>
          <TeamMappingItem
            fromTeamKey={teamKeys[0]}
            toTeamKey={teamKeys[1]}
            removeTeamMap={props.removeTeamMap}
          />
        </li>)
      }
    </ul>
  </div>
)

TeamMappingsList.propTypes = {
  teamMappings: PropTypes.object.isRequired,
  removeTeamMap: PropTypes.func.isRequired,
}

export default TeamMappingsList
