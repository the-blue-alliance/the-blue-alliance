import React from 'react'
import AppBar from 'material-ui/AppBar'
import LayoutDropdownMaterial from './LayoutDropdownMaterial'
import FlatButton from 'material-ui/FlatButton'

const GamedayNavbarMaterial = (props) => (
  <AppBar
    title='GameDay'
    showMenuIconButton={false}
    iconElementRight={<div>
      <FlatButton label='Set Layout' />
      <FlatButton label='Set Layout 2' />
      </div>/*<LayoutDropdownMaterial />*/}
      />
)

export default GamedayNavbarMaterial
