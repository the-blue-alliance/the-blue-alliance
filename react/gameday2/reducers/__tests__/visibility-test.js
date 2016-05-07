jest.unmock('../visibility')
jest.unmock('../../constants/ActionTypes')

import visibility from '../visibility'
import * as types from '../../constants/ActionTypes'

describe('visibility reducer', () => {
  it('defaults all views to not visibile', () => {
    const expectedState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    expect(visibility(undefined, {})).toEqual(expectedState)
  })

  it('toggles chat panel from false to true', () => {
    const initialState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    const expectedState = {
      hashtagPanel: false,
      chatPanel: true,
      tickerPanel: false
    }
    const action = {
      type: types.TOGGLE_CHAT_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles chat panel from true to false', () => {
    const initialState = {
      hashtagPanel: false,
      chatPanel: true,
      tickerPanel: false
    }
    const expectedState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    const action = {
      type: types.TOGGLE_CHAT_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles hashtag panel from false to true', () => {
    const initialState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    const expectedState = {
      hashtagPanel: true,
      chatPanel: false,
      tickerPanel: false
    }
    const action = {
      type: types.TOGGLE_HASHTAG_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles hashtag panel from true to false', () => {
    const initialState = {
      hashtagPanel: true,
      chatPanel: false,
      tickerPanel: false
    }
    const expectedState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    const action = {
      type: types.TOGGLE_HASHTAG_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles ticker panel from false to true', () => {
    const initialState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    const expectedState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: true
    }
    const action = {
      type: types.TOGGLE_TICKER_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('toggles ticker panel from true to false', () => {
    const initialState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: true
    }
    const expectedState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: false
    }
    const action = {
      type: types.TOGGLE_TICKER_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('hides ticker panel when showing hashtag panel', () => {
    const initialState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: true
    }
    const expectedState = {
      hashtagPanel: true,
      chatPanel: false,
      tickerPanel: false
    }
    const action = {
      type: types.TOGGLE_HASHTAG_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })

  it('hides hashtag panel when showing ticker panel', () => {
    const initialState = {
      hashtagPanel: true,
      chatPanel: false,
      tickerPanel: false
    }
    const expectedState = {
      hashtagPanel: false,
      chatPanel: false,
      tickerPanel: true
    }
    const action = {
      type: types.TOGGLE_TICKER_PANEL_VISIBILITY
    }
    expect(visibility(initialState, action)).toEqual(expectedState)
  })
})
