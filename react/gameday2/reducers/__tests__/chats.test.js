import chats from '../chats'
import { SET_TWITCH_CHAT } from '../../constants/ActionTypes'

describe('chats reducer', () => {
  const defaultState = {
    chats: {
      firstupdatesnow: {
        name: 'FIRST Updates Now',
        channel: 'firstupdatesnow',
      },
    },
    renderedChats: ['firstupdatesnow'],
    currentChat: 'firstupdatesnow',
    defaultChat: 'firstupdatesnow',
  }

  it('defaults to the appropriate state', () => {
    expect(chats(undefined, {})).toEqual(defaultState)
  })

  it('sets the current chat', () => {
    const initialState = {
      chats: {
        chat1: {
          name: 'Chat 1',
          channel: 'chat1',
        },
        chat2: {
          name: 'Chat 2',
          channel: 'chat2',
        },
      },
      renderedChats: ['chat1'],
      currentChat: 'chat1',
    }

    const expectedState = Object.assign({}, initialState, {
      renderedChats: ['chat1', 'chat2'],
      currentChat: 'chat2',
    })

    const action = {
      type: SET_TWITCH_CHAT,
      channel: 'chat2',
    }

    expect(chats(initialState, action)).toEqual(expectedState)
  })

  it('does not render an already-rendered chat again', () => {
    const initialState = {
      chats: {
        chat1: {
          name: 'Chat 1',
          channel: 'chat1',
        },
        chat2: {
          name: 'Chat 2',
          channel: 'chat2',
        },
      },
      renderedChats: ['chat1', 'chat2'],
      currentChat: 'chat1',
    }

    const expectedState = Object.assign({}, initialState, {
      renderedChats: ['chat1', 'chat2'],
      currentChat: 'chat2',
    })

    const action = {
      type: SET_TWITCH_CHAT,
      channel: 'chat2',
    }

    expect(chats(initialState, action)).toEqual(expectedState)
  })
})
