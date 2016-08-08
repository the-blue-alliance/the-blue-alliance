import React from 'react'
import classNames from 'classnames'

export default React.createClass({
  componentDidMount() {
    !function (d, s, id) {
      let js, fjs = d.getElementsByTagName(s)[0], p = /^http:/.test(d.location) ? 'http' : 'https'
      if (!d.getElementById(id)) {
        js = d.createElement(s); js.id = id
        js.src = p + '://platform.twitter.com/widgets.js'
        fjs.parentNode.insertBefore(js, fjs)
      }
    }(document, 'script', 'twitter-wjs')
  },
  render() {
    const classes = classNames({
      'hidden': !this.props.enabled,
      'hashtag-sidebar': true,
    })
    return (
      <div className={classes}>
        <div id="twitter-widget"><a className="twitter-timeline" href="https://twitter.com/search?q=%23omgrobots" data-widget-id="406597120632709121">Tweets about "#omgrobots"</a></div>
      </div>
    )
  },
})
