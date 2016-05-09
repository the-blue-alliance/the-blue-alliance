jest.unmock('../../constants/ActionTypes')
//jest.unmock('../../constants/LayoutConstants')
jest.unmock('../displayedWebcasts')

import * as types from '../../constants/ActionTypes'
import { MAX_SUPPORTED_VIEWS } from '../../constants/LayoutConstants'
import displayedWebcasts from '../displayedWebcasts'

describe('displayedWebcasts reducer', () => {

  it('defaults to an empty array', () => {
    let state = displayedWebcasts(undefined, {})
    expect(displayedWebcasts(undefined, {})).toEqual([])
  })

  if('handles webcast reset', () => {
    let initialState = ['a', 'b', 'c']
    let action = {
      type: types.RESET_WEBCASTS
    }
    expect(displayedWebcasts(initialState, action)).toEqual([])
  })

  it('adds a webcast to the beginning of an empty list', () => {
    let action = {
      type: types.ADD_WEBCAST,
      webcastId: 'a'
    }
    expect(displayedWebcasts(undefined, action)).toEqual(['a'])
  })

  it('adds a webcast at the first available space', () => {
    let action = {
      type: types.ADD_WEBCAST,
      webcastId: 'b'
    }
    let initialState = ['a', null, 'c']
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', 'c'])
  })

  it('adds a webcast to the end of the list if space is available', () => {
    let action = {
      type: types.ADD_WEBCAST,
      webcastId: 'd'
    }
    let initialState = ['a', 'b', 'c']
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', 'c', 'd'])
  })

  it('doesn\'t add a webcast if the list alreadt contains MAX_SUPPORTED_VIEWS elements', () => {
    let initialState = []
    for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
      initialState.push(i)
    }

    let action = {
      type: types.ADD_WEBCAST,
      webcastId: 'a'
    }

    expect(displayedWebcasts(initialState, action)).toEqual(initialState)
  })

  it('removes a webcast by replacing it with null', () => {
    let initialState = ['a', 'b', 'c', 'd']
    let action = {
      type: types.REMOVE_WEBCAST,
      webcastId: 'c'
    }
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', null, 'd'])
  })

  it('adds webcast with a specified location', () => {
    let initialState = ['a', 'b', 'c', 'd']
    let action = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId: 'z',
      location: 1
    }
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'z', 'c', 'd'])
  })

  it('adds webcast with a specified location, expanding and filling the array with null if needed', () => {
    let initialState = ['a', 'b']
    let action = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId: 'z',
      location: 4
    }
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', null, null, 'z'])
  })

  it('doesn\'t add a webcast with a specified location if the location is >= MAX_SUPPORTED_VIEWS', () => {
    let initialState = []
    for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
      initialState.push(i)
    }

    let action = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId: 'a',
      location: MAX_SUPPORTED_VIEWS
    }

    expect(displayedWebcasts(initialState, action)).toEqual(initialState)
  })

  it('swaps the location of two webcasts', () => {
    let initialState = ['a', 'b']
    let expectedState = ['b', 'a']
    let action = {
      type: types.SWAP_WEBCASTS,
      firstLocation: 0,
      secondLocation: 1
    }
    expect(displayedWebcasts(initialState, action)).toEqual(expectedState)
  })
})
