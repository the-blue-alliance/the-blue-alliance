jest.unmock('../chatPanelVisible')
jest.unmock('../../constants/ActionTypes')

import chatPanelVisible from '../chatPanelVisible'
import { TOGGLE_CHAT_PANEL_VISIBILITY } from '../../constants/ActionTypes'

describe('chatPanelVisible reducer', () => {
  it('defaults to false', () => {
    expect(chatPanelVisible(undefined, {})).toBe(false)
  })

  it('toggles from false to true', () => {
    let initialState = false
    let action = {
      type: TOGGLE_CHAT_PANEL_VISIBILITY
    }
    expect(chatPanelVisible(initialState, action)).toBe(true)
  })

  it('toggles from true to false', () => {
    let initialState = true
    let action = {
      type: TOGGLE_CHAT_PANEL_VISIBILITY
    }
    expect(chatPanelVisible(initialState, action)).toBe(false)
  })
})
