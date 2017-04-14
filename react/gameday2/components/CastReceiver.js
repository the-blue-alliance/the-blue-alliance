/* global cast */
import React, { PropTypes } from 'react'
import Script from 'react-load-script'

export default class CastReceiver extends React.Component {
  static propTypes = {
    setLayout: PropTypes.func.isRequired,
    addWebcastAtPosition: PropTypes.func.isRequired,
  }

  render() {
    console.log("cast render")
    return (
      <Script
        url="https://www.gstatic.com/cast/sdk/libs/receiver/2.0.0/cast_receiver.js"
        onCreate={this.handleScriptCreate.bind(this)}
        onError={this.handleScriptError.bind(this)}
        onLoad={this.handleScriptLoad.bind(this)}
      />
    )
  }

  handleScriptCreate() {
    console.log("Loading chromecast receiver API...")
  }

  handleScriptError() {
    console.log("error loading chromecast receiver")
  }

  handleScriptLoad() {
    console.log("setting layout")
    this.props.setLayout(0)

    console.log("loaded chromecast receiver")
    let castReceiver = cast.receiver.CastReceiverManager.getInstance()
    let messageBus = castReceiver.getCastMessageBus('urn:x-cast:com.thebluealliance.cast')

    console.log("configuring callbacks")
    castReceiver.onReady = this.castOnReady.bind(this)
    castReceiver.onSenderConnected = this.castOnSenderConnected.bind(this)
    castReceiver.onSenderDisconnected = this.castOnSenderDisconnected.bind(this)
    castReceiver.onSystemVolumeChanged = this.castOnSystemVolumeChanged.bind(this)
    messageBus.onMessage = this.castOnMessage.bind(this)

    console.log("starting receiver")
    castReceiver.start({statusText: "Application is starting"});
    this.setState({castAPI: castReceiver, castMessageBus: messageBus})
    console.log('Receiver Manager started');
  }

  castOnReady(event) {
    console.log('Received Ready event: ' + JSON.stringify(event.data))
  }

  castOnSenderConnected(event) {
    console.log('Received Sender Connected event: ' + event.data)
    console.log(window.castReceiverManager.getSender(event.data).userAgent)
  }

  castOnSenderDisconnected(event) {
    console.log('Received Sender Disconnected event: ' + event.data)
  }

  castOnSystemVolumeChanged(event) {
    console.log('Received System Volume Changed event: ' + event.data['level'] + ' ' + event.data['muted'])
  }

  castOnMessage(event) {
    console.log('Message [' + event.senderId + ']: ' + event.data)
    this.props.addWebcastAtPosition("firstupdatesnow-0", 0);
  }
}
