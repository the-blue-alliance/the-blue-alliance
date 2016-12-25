import chats from '../chats'
import { SET_TWITCH_CHAT } from '../../constants/ActionTypes'

describe('chats reducer', () => {
  const defaultState = {
    chats: [
      {
        name: 'GameDay',
        channel: 'tbagameday',
        rendered: true,
      },
    ],
    currentChat: 'tbagameday',
  }

  it('defaults to the appropriate state', () => {
    expect(chats(undefined, {})).toEqual(defaultState)
  })

  it('sets the current chat', () => {
    const initialState = {
      chats: [
        {
          name: 'Chat 1',
          channel: 'chat1',
          rendered: true,
        },
        {
          name: 'Chat 2',
          channel: 'chat2',
          rendered: false,
        },
      ],
      currentChat: 'chat1',
    }

    const expectedState = Object.assign({}, initialState, {
      currentChat: 'chat2',
    })
    expectedState.chats[1].rendered = true

    const action = {
      type: SET_TWITCH_CHAT,
      channel: 'chat2',
    }

    expect(chats(initialState, action)).toEqual(expectedState)
  })
})
