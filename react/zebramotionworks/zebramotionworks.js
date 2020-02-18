import React from 'react'
import ReactDOM from 'react-dom'
import ZebraMotionWorksVisualizer from './components/ZebraMotionWorksVisualizer'

const els = document.getElementsByClassName('zebramotionworks-content')
for (let i = 0; i < els.length; i++) {
  const el = els[i]
  const zebraData = JSON.parse(el.getAttribute('data-zebramotionworks'))
  const year = parseInt(el.getAttribute('data-year'), 10)
  ReactDOM.render(
    <ZebraMotionWorksVisualizer data={zebraData} year={year} />,
    el
  )
}
