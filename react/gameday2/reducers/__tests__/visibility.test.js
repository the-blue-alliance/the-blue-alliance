jest.unmock('../visibility')
jest.unmock('../../constants/ActionTypes')

import visibility from '../visibility'
import * as types from '../../constants/ActionTypes'

describe('visibility reducer', () => {
  it('defaults all views to not visibile', () => {
    const expectedState = {
      hashtagSidebar: false,
      chatSidebar: false,
      tickerSidebar: false
    }
    expect(visibility(undefined, {})).toEqual(expectedState)
  })

  it('toggles chat sidebar from false to true', () => {
    const initialState = {
      hashtagSidebar: false,
      chatSidebar: false,
      tickerSidebar: false
    }
    const expectedState = {
      hashtagSidebar: false,
      chatSidebar: true,
      tickerSidebar: false
    }
    const action = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles chat sidebar from true to false', () => {
    const initialState = {
      hashtagSidebar: false,
      chatSidebar: true,
      tickerSidebar: false
    }
    const expectedState = {
      hashtagSidebar: false,
      chatSidebar: false,
      tickerSidebar: false
    }
    const action = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles hashtag sidebar from false to true', () => {
    const initialState = {
      hashtagSidebar: false,
      chatSidebar: false,
      tickerSidebar: false
    }
    const expectedState = {
      hashtagSidebar: true,
      chatSidebar: false,
      tickerSidebar: false
    }
    const action = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles hashtag sidebar from true to false', () => {
    const initialState = {
      hashtagSidebar: true,
      chatSidebar: false,
      tickerSidebar: false
    }
    const expectedState = {
      hashtagSidebar: false,
      chatSidebar: false,
      tickerSidebar: false
    }
    const action = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })
})
