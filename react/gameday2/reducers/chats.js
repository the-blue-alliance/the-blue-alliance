import {
  SET_TWITCH_CHAT,
  SET_DEFAULT_TWITCH_CHAT,
  WEBCASTS_UPDATED,
} from '../constants/ActionTypes'

/**
 * @typedef {Object} Chat
 * @property {string} name - A human-readable name for this chat; typically the
 * associated event/webcast name.
 * @property {string} channel - The Twitch channel of this chat.
 **/

/**
 * @typedef {Object} ChatsState
 * @property {Chat[]} chats - Array containing all chats.
 * @property {string[]} renderedChats - Array containing channels of all chats
 * that have been rendered to the DOM. This lets us keep previously viewed
 * chats in the DOM, but hidden, to make swapping between them quicker.
 * NOTE: This is assumed to be an append-only array: once a channel is pushed
 * to this array, that value, and its position, should never change.
 * @property {string} currentChat - The channel of the currently visible chat.
 */

// Default to having the GameDay chat as the only chat
const defaultChat = {
  name: 'FIRST Updates Now',
  channel: 'firstupdatesnow',
}

const defaultState = {
  chats: {
    [defaultChat.channel]: Object.assign({}, defaultChat),
  },
  renderedChats: ['firstupdatesnow'],
  currentChat: 'firstupdatesnow',
  defaultChat: 'firstupdatesnow',
}

const setChatsFromWebcasts = (webcasts, state) => {
  const newState = Object.assign({}, defaultState)
  newState.currentChat = state.currentChat
  newState.renderedChats = state.renderedChats

  Object.keys(webcasts).forEach((key) => {
    const webcast = webcasts[key]

    // Don't add BlueZone to chat
    if (webcast.key === 'bluezone') {
      return
    }

    if (webcast.type === 'twitch') {
      // We found a twitch webcast!
      newState.chats[webcast.channel] = {
        name: webcast.name,
        channel: webcast.channel,
      }
    }
  })

  return newState
}

const setTwitchChat = (channel, state) => {
  // Verify that the desired chat exists in the list of known chats
  if (state.chats[channel] === undefined) {
    // Chat does not exist
    return state
  }

  // If the chat has not yet been rendered, add it to the list of chats that
  // should be rendered to the DOM
  const renderedChats = state.renderedChats.slice(0)
  if (renderedChats.indexOf(channel) === -1) {
    renderedChats.push(channel)
  }

  return Object.assign({}, state, {
    renderedChats,
    currentChat: channel,
  })
}

const setDefaultTwitchChat = (channel, state) => {
  // Verify that the desired chat exists in the list of known chats
  if (state.chats[channel] === undefined) {
    // Chat does not exist
    return state
  }

  return Object.assign({}, state, {
    defaultChat: channel,
  })
}

const chats = (state = defaultState, action) => {
  switch (action.type) {
    case WEBCASTS_UPDATED:
      return setChatsFromWebcasts(action.webcasts, state)
    case SET_TWITCH_CHAT:
      return setTwitchChat(action.channel, state)
    case SET_DEFAULT_TWITCH_CHAT:
      return setDefaultTwitchChat(action.channel, state)
    default:
      return state
  }
}

export default chats
