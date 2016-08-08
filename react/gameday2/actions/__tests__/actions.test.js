import * as types from '../../constants/ActionTypes'
import * as actions from '../index'

describe('actions', () => {
  it('should create an action to set webcsts from raw data', () => {
    const webcasts = 'webcast string'
    const expectedAction = {
      type: types.SET_WEBCASTS_RAW,
      webcasts,
    }
    expect(actions.setWebcastsRaw(webcasts)).toEqual(expectedAction)
  })

  it('should create an action to toggle the hashtag sidebar visibility', () => {
    const expectedAction = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
    }
    expect(actions.toggleHashtagSidebarVisibility()).toEqual(expectedAction)
  })

  it('should create an action to toggle the chat sidebar visibility', () => {
    const expectedAction = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
    }
    expect(actions.toggleChatSidebarVisibility()).toEqual(expectedAction)
  })

  it('should create an action to add a webcast if the webcast ID exists in webcastsById', () => {
    const webcastId = 'a'
    const getState = () => ({
      webcastsById: {
        [webcastId]: {},
      },
    })
    const dispatch = jasmine.createSpy()
    actions.addWebcast(webcastId)(dispatch, getState)
    expect(dispatch).toHaveBeenCalledWith({
      type: types.ADD_WEBCAST,
      webcastId,
    })
  })

  it('should not create an action to add a webcast if the webcast ID does not exist in webcastsById', () => {
    const getState = () => ({
      webcastsById: {},
    })
    const dispatch = jasmine.createSpy()
    actions.addWebcast('a')(dispatch, getState)
    expect(dispatch.calls.any()).toBe(false)
  })

  it('should create an action to add a webcast at a specific location if the webcast ID exists in webcastsById', () => {
    const webcastId = 'a'
    const location = 0
    const getState = () => ({
      webcastsById: {
        [webcastId]: {},
      },
    })
    const dispatch = jasmine.createSpy()
    actions.addWebcastAtLocation(webcastId, location)(dispatch, getState)
    expect(dispatch).toHaveBeenCalledWith({
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId,
      location,
    })
  })

  it('should not create an action to add a webcast at a specific location if the webcast ID does not exist in webcastsById', () => {
    const webcastId = 'a'
    const location = 0
    const getState = () => ({
      webcastsById: {},
    })
    const dispatch = jasmine.createSpy()
    actions.addWebcastAtLocation(webcastId, location)(dispatch, getState)
    expect(dispatch.calls.any()).toBe(false)
  })

  it('should create an action to swap two webcasts', () => {
    const firstLocation = 0
    const secondLocation = 1
    const expectedAction = {
      type: types.SWAP_WEBCASTS,
      firstLocation,
      secondLocation,
    }
    expect(actions.swapWebcasts(firstLocation, secondLocation)).toEqual(expectedAction)
  })

  it('should create an action to remove a specified webcast', () => {
    const webcastId = 'a'
    const expectedAction = {
      type: types.REMOVE_WEBCAST,
      webcastId,
    }
    expect(actions.removeWebcast(webcastId)).toEqual(expectedAction)
  })

  it('should create an action to reset all webcasts', () => {
    const expectedAction = {
      type: types.RESET_WEBCASTS,
    }
    expect(actions.resetWebcasts()).toEqual(expectedAction)
  })

  it('should create an action to set the layout', () => {
    const layoutId = 3
    const expectedAction = {
      type: types.SET_LAYOUT,
      layoutId,
    }
    expect(actions.setLayout(layoutId)).toEqual(expectedAction)
  })
})
