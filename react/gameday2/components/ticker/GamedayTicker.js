import React from 'react'
let Firebase = require('firebase')
let ReactFireMixin = require('reactfire')

const GamedayTicker = React.createClass({
  mixins: [ReactFireMixin],
  componentWillMount: function() {
    let ref = new Firebase('https://thebluealliance.firebaseio.com/notifications/')
    ref.limitToLast(5)
    this.bindAsArray(ref, 'notifications')
  }
})

export default GamedayTicker
