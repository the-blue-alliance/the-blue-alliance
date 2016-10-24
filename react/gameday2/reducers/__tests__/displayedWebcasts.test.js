import * as types from '../../constants/ActionTypes'
import { MAX_SUPPORTED_VIEWS } from '../../constants/LayoutConstants'
import displayedWebcasts from '../displayedWebcasts'

describe('displayedWebcasts reducer', () => {
  it('defaults to an empty array', () => {
    expect(displayedWebcasts(undefined, {})).toEqual([])
  })

  it('handles webcast reset', () => {
    const initialState = ['a', 'b', 'c']
    const action = {
      type: types.RESET_WEBCASTS,
    }
    expect(displayedWebcasts(initialState, action)).toEqual([])
  })

  it('adds a webcast to the beginning of an empty list', () => {
    const action = {
      type: types.ADD_WEBCAST,
      webcastId: 'a',
    }
    expect(displayedWebcasts(undefined, action)).toEqual(['a'])
  })

  it('adds a webcast at the first available space', () => {
    const action = {
      type: types.ADD_WEBCAST,
      webcastId: 'b',
    }
    const initialState = ['a', null, 'c']
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', 'c'])
  })

  it('adds a webcast to the end of the list if space is available', () => {
    const action = {
      type: types.ADD_WEBCAST,
      webcastId: 'd',
    }
    const initialState = ['a', 'b', 'c']
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', 'c', 'd'])
  })

  it('doesn\'t add a webcast if the list alreadt contains MAX_SUPPORTED_VIEWS elements', () => {
    const initialState = []
    for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
      initialState.push(i)
    }

    const action = {
      type: types.ADD_WEBCAST,
      webcastId: 'a',
    }

    expect(displayedWebcasts(initialState, action)).toEqual(initialState)
  })

  it('removes a webcast by replacing it with null', () => {
    const initialState = ['a', 'b', 'c', 'd']
    const action = {
      type: types.REMOVE_WEBCAST,
      webcastId: 'c',
    }
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', null, 'd'])
  })

  it('adds webcast with a specified location', () => {
    const initialState = ['a', 'b', 'c', 'd']
    const action = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId: 'z',
      location: 1,
    }
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'z', 'c', 'd'])
  })

  it('adds webcast with a specified location, expanding and filling the array with null if needed', () => {
    const initialState = ['a', 'b']
    const action = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId: 'z',
      location: 4,
    }
    expect(displayedWebcasts(initialState, action)).toEqual(['a', 'b', null, null, 'z'])
  })

  it('doesn\'t add a webcast with a specified location if the location is >= MAX_SUPPORTED_VIEWS', () => {
    const initialState = []
    for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
      initialState.push(i)
    }

    const action = {
      type: types.ADD_WEBCAST_AT_LOCATION,
      webcastId: 'a',
      location: MAX_SUPPORTED_VIEWS,
    }

    expect(displayedWebcasts(initialState, action)).toEqual(initialState)
  })

  it('swaps the location of two webcasts', () => {
    const initialState = ['a', 'b']
    const expectedState = ['b', 'a']
    const action = {
      type: types.SWAP_WEBCASTS,
      firstLocation: 0,
      secondLocation: 1,
    }
    expect(displayedWebcasts(initialState, action)).toEqual(expectedState)
  })
})
