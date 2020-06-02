import React from 'react'
import { Card, CardActions, CardHeader, CardText } from 'material-ui/Card'
import RaisedButton from 'material-ui/RaisedButton'
import { webcastPropType } from '../../utils/webcastUtils'

const EmbedDirectLink = (props) => {
  const directLink = props.webcast.channel
  const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translateX(-50%) translateY(-50%)',
  }

  return (
    <Card style={style}>
      <CardHeader
        title="Webcast could not be embedded"
      />
      <CardText>
        Due to technical or copyright issues, the webcast cannot be displayed in TBA GameDay.
      </CardText>
      <CardActions>
        <RaisedButton href={directLink} target="_blank" label="Open in new tab" />
      </CardActions>
    </Card>
  )
}

EmbedDirectLink.propTypes = {
  webcast: webcastPropType.isRequired,
}

export default EmbedDirectLink
