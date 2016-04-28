jest.unmock('../index')

import * as types from '../../constants/ActionTypes'
import * as actions from '../index'

describe('actions', () => {
  it('should create an action to set webcsts from raw data', () => {
    let webcasts = "webcast string"
    let expectedAction = {
      type: types.SET_WEBCASTS_RAW,
      webcasts
    }
    expect(actions.setWebcastsRaw(webcasts)).toEqual(expectedAction)
  })

  it('should create an action to toggle the hashtag panel visibility', () => {
    let expectedAction = {
      type: types.TOGGLE_HASHTAG_PANEL_VISIBILITY
    }
    expect(actions.toggleHashtagPanelVisibility()).toEqual(expectedAction)
  })

  it('should create an action to toggle the chat panel visibility', () => {
    let expectedAction = {
      type: types.TOGGLE_CHAT_PANEL_VISIBILITY
    }
    expect(actions.toggleChatPanelVisibility()).toEqual(expectedAction)
  })

  it('should create an action to add a webcast', () => {
    let webcastId = 'a'
    let expectedAction = {
      type: types.ADD_WEBCAST,
      id: webcastId
    }
    expect(actions.addWebcast(webcastId)).toEqual(expectedAction)
  })

  it('should create an action to add a webcast at a specific location', () => {
    let webcastId = 'a'
    let location = 3
    let expectedAction = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId,
      location
    }
    expect(actions.addWebcastAtLocation(webcastId, location)).toEqual(expectedAction)
  })

  it('should create an action to remove a specified webcast', () => {
    let webcastId = 'a'
    let expectedAction = {
      type: types.REMOVE_WEBCAST,
      id: webcastId
    }
    expect(actions.removeWebcast(webcastId)).toEqual(expectedAction)
  })

  if('should create an action to reset all webcasts', () => {
    let expectedAction = {
      type: types.RESET_WEBCASTS
    }
    expect(actions.resetWebcasts()).toEqual(expectedAction)
  })

  it('should create an action to set the layout', () => {
    let layoutId = 3
    let expectedAction = {
      type: types.SET_LAYOUT,
      layoutId
    }
    expect(actions.setLayout(layoutId)).toEqual(expectedAction)
  })
})
