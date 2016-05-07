import React, { PropTypes } from 'react'
let Firebase = require('firebase')
let ReactFireMixin = require('reactfire')

const GamedayTicker = React.createClass({
  mixins: [ReactFireMixin],
  propTypes: {
    enabled: PropTypes.bool.isRequired
  },
  componentWillMount: function() {
    let ref = new Firebase('https://thebluealliance.firebaseio.com/notifications/')
    ref.limitToLast(5)
    this.bindAsArray(ref, 'notifications')
  }
})

export default GamedayTicker
