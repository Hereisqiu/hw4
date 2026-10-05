// Lets any page open the chat (optionally sending a question) without prop drilling.
export const OPEN_CHAT = 'cc:open-chat'

export function openChat(question?: string) {
  window.dispatchEvent(new CustomEvent(OPEN_CHAT, { detail: question }))
}
