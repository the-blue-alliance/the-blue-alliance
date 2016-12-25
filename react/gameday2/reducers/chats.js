import { SET_TWITCH_CHAT } from '../constants/ActionTypes'

/**
 * @typedef {Object} Chat
 * @property {string} name - A human-readable name for this chat; typically the
 * associated event/webcast name.
 * @property {string} channel - The Twitch channel of this chat.
 * @property {boolean} rendered - If this chat should be rendered to the DOM.
 * Used to keep track of chats that have been displayed before so we can avoid
 * having to reload the embed whenever the user switches chats while still
 * allowing us to lazy-load chat embeds as needed.
 **/

/**
 * @typedef {Object} ChatsState
 * @property {Chat[]} chats - Array containing all chats
 * @property {string} currentChat - The channel of the currently visible chat
 * @property {boolean} chatPanelHasBeenOpen - If the chat panel has been open before; used to optimize loading
 */

// Default to having the GameDay chat as the only chat
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

const setTwitchChat = (channel, state) => {
  // Verify that the desired chat exists in the list of known chats
  const chats = state.chats.slice(0)
  const chat = chats.find((chat) => chat.channel === channel)
  if (chat === undefined) {
    // Chat does not exist
    return state
  }

  chat.rendered = true

  return Object.assign({}, state, {
    chats,
    currentChat: channel,
  })
}

const chats = (state = defaultState, action) => {
  switch (action.type) {
    case SET_TWITCH_CHAT:
      return setTwitchChat(action.channel, state)
    default:
      return state
  }
}

export default chats
