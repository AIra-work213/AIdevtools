import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { useSettingsStore } from './settingsStore'

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    code?: string
    testCases?: any[]
    validation?: any
    generationSettings?: any
  }
}

interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  currentResponse: string
  sessionId: string

  // Actions
  sendMessage: (content: string, file?: File) => Promise<void>
  clearChat: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  appendMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  regenerateLastResponse: () => Promise<void>
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      messages: [],
      isLoading: false,
      error: null,
      currentResponse: '',
      sessionId: Date.now().toString(),

      sendMessage: async (content: string, file?: File) => {
        set({ isLoading: true, error: null, currentResponse: '' })

        try {
          const settings = useSettingsStore.getState().generationSettings

          // Add user message
          const userMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
            type: 'user',
            content: file ? `${content}\n\n[Прикреплен файл: ${file.name}]` : content,
          }
          get().appendMessage(userMessage)

          // Get conversation history (last 10 messages for context)
          const conversationHistory = get().messages.slice(-10)

          // Call API with settings and context
          const response = await fetch('/api/v1/generate/manual', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              requirements: content,
              metadata: {
                feature: 'User Generated',
                owner: 'QA Engineer',
              },
              generation_settings: settings,
              conversation_history: conversationHistory,
            }),
          })

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
            console.error('API Error:', response.status, errorData)
            throw new Error(`Failed to generate response: ${response.status} ${JSON.stringify(errorData)}`)
          }

          const data = await response.json()

          // Add assistant message
          const assistantMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
            type: 'assistant',
            content: 'Тесты успешно сгенерированы. Проверьте код в редакторе справа.',
            metadata: {
              code: data.code,
              testCases: data.test_cases,
              validation: data.validation,
              generationSettings: settings,
            },
          }
          get().appendMessage(assistantMessage)

          set({ currentResponse: data.code })
        } catch (error) {
          console.error('Error sending message:', error)
          set({ error: 'Произошла ошибка при отправке сообщения' })

          // Add error message
          const errorMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
            type: 'assistant',
            content: 'Извините, произошла ошибка. Попробуйте еще раз.',
          }
          get().appendMessage(errorMessage)
        } finally {
          set({ isLoading: false })
        }
      },

      regenerateLastResponse: async () => {
        const { messages } = get()
        if (messages.length < 2) return

        const lastUserMessage = messages[messages.length - 2]
        if (lastUserMessage.type !== 'user') return

        // Remove last assistant message
        set((state) => ({
          messages: state.messages.slice(0, -1),
        }))

        // Resend with same content
        get().sendMessage(lastUserMessage.content)
      },

      clearChat: () => {
        set({
          messages: [],
          currentResponse: '',
          error: null,
          sessionId: Date.now().toString()
        })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      setError: (error: string | null) => {
        set({ error })
      },

      appendMessage: (message) => {
        const newMessage: ChatMessage = {
          ...message,
          id: Date.now().toString(),
          timestamp: new Date(),
        }
        set((state) => ({
          messages: [...state.messages, newMessage],
        }))
      },
    }),
    {
      name: 'chat-store',
    }
  )
)