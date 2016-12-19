import React, { PropTypes } from 'react'
import classNames from 'classnames'

export default class HashtagSidebar extends React.Component {
  static propTypes = {
    enabled: PropTypes.bool,
  }

  componentDidMount() {
    (function twitterEmbed(d, s, id) {
      const fjs = d.getElementsByTagName(s)[0]
      const p = /^http:/.test(d.location) ? 'http' : 'https'
      if (!d.getElementById(id)) {
        const js = d.createElement(s); js.id = id
        /* eslint-disable prefer-template */
        js.src = p + '://platform.twitter.com/widgets.js'
        /* eslint-enable prefer-template */
        fjs.parentNode.insertBefore(js, fjs)
      }
    }(document, 'script', 'twitter-wjs'))
  }

  render() {
    const classes = classNames({
      'hashtag-sidebar': true,
    })
    const style = {
      display: this.props.enabled ? null : 'none',
    }

    return (
      <div className={classes} style={style}>
        <div id="twitter-widget">
          <a className="twitter-timeline" href="https://twitter.com/search?q=%23omgrobots" data-widget-id="406597120632709121">Tweets about #omgrobots</a>
        </div>
      </div>
    )
  }
}
