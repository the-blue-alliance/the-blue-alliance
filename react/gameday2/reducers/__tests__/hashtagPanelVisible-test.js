jest.unmock('../hashtagPanelVisible')
jest.unmock('../../constants/ActionTypes')

import hashtagPanelVisible from '../hashtagPanelVisible'
import { TOGGLE_HASHTAG_PANEL_VISIBILITY } from '../../constants/ActionTypes'

describe('hashtagPanelVisible reducer', () => {
  it('defaults to false', () => {
    expect(hashtagPanelVisible(undefined, {})).toBe(false)
  })

  it('toggles from false to true', () => {
    let initialState = false
    let action = {
      type: TOGGLE_HASHTAG_PANEL_VISIBILITY
    }
    expect(hashtagPanelVisible(initialState, action)).toBe(true)
  })

  it('toggles from true to false', () => {
    let initialState = true
    let action = {
      type: TOGGLE_HASHTAG_PANEL_VISIBILITY
    }
    expect(hashtagPanelVisible(initialState, action)).toBe(false)
  })
})
