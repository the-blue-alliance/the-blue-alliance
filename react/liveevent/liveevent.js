import React from 'react'
import ReactDOM from 'react-dom'
import LiveEventPanel from './components/LiveEventPanel'

const el = document.getElementById('liveevent-content')

ReactDOM.render(
  <LiveEventPanel eventKey={el.getAttribute('data-eventkey')} />,
  el
)
