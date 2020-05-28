import React from 'react'
import ReactDOM from 'react-dom'
import LiveEventPanel from './components/LiveEventPanel'

const els = document.getElementsByClassName('liveevent-content')
for (let i = 0; i < els.length; i++) {
  const el = els[i]
  ReactDOM.render(
    <LiveEventPanel
      eventKey={el.getAttribute('data-eventkey')}
      simple={el.getAttribute('data-simple') !== null}
    />,
    el
  )
}
