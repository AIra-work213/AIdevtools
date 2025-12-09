import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { ChatMessage } from './chatStore'

interface ChatHistory {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: Date
  updatedAt: Date
  metadata?: {
    code?: string
    testCases?: any[]
    generationSettings?: any
  }
}

interface HistoryState {
  chatHistory: ChatHistory[]

  // Actions
  saveChat: (title: string, messages: ChatMessage[], metadata?: any) => string
  deleteChat: (id: string) => void
  loadChat: (id: string) => ChatHistory | undefined
  updateChatTitle: (id: string, title: string) => void
  clearHistory: () => void
  exportChat: (id: string) => string
}

export const useHistoryStore = create<HistoryState>()(
  devtools(
    persist(
      (set, get) => ({
        chatHistory: [],

        saveChat: (title: string, messages: ChatMessage[], metadata?: any) => {
          const chatId = Date.now().toString()
          const newChat: ChatHistory = {
            id: chatId,
            title,
            messages,
            createdAt: new Date(),
            updatedAt: new Date(),
            metadata
          }

          set((state) => ({
            chatHistory: [newChat, ...state.chatHistory].slice(0, 100) // Keep last 100 chats
          }))

          return chatId
        },

        deleteChat: (id: string) => {
          set((state) => ({
            chatHistory: state.chatHistory.filter(chat => chat.id !== id)
          }))
        },

        loadChat: (id: string) => {
          return get().chatHistory.find(chat => chat.id === id)
        },

        updateChatTitle: (id: string, title: string) => {
          set((state) => ({
            chatHistory: state.chatHistory.map(chat =>
              chat.id === id ? { ...chat, title, updatedAt: new Date() } : chat
            )
          }))
        },

        clearHistory: () => {
          set({ chatHistory: [] })
        },

        exportChat: (id: string) => {
          const chat = get().chatHistory.find(c => c.id === id)
          if (!chat) return ''

          const exportData = {
            title: chat.title,
            createdAt: chat.createdAt.toISOString(),
            updatedAt: chat.updatedAt.toISOString(),
            messages: chat.messages.map(msg => ({
              type: msg.type,
              content: msg.content,
              timestamp: msg.timestamp.toISOString(),
              metadata: msg.metadata
            }))
          }

          return JSON.stringify(exportData, null, 2)
        }
      }),
      {
        name: 'chat-history',
        partialize: (state) => ({ chatHistory: state.chatHistory }),
        // Fix date deserialization from localStorage
        onRehydrateStorage: () => (state) => {
          if (state?.chatHistory) {
            state.chatHistory = state.chatHistory.map(chat => ({
              ...chat,
              createdAt: new Date(chat.createdAt),
              updatedAt: new Date(chat.updatedAt),
              messages: chat.messages.map(msg => ({
                ...msg,
                timestamp: new Date(msg.timestamp)
              }))
            }))
          }
        }
      }
    ),
    {
      name: 'history-store',
    }
  )
)