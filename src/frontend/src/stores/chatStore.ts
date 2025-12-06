import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    code?: string
    testCases?: any[]
    validation?: any
  }
}

interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  currentResponse: string

  // Actions
  sendMessage: (content: string, file?: File) => Promise<void>
  clearChat: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  appendMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      messages: [],
      isLoading: false,
      error: null,
      currentResponse: '',

      sendMessage: async (content: string, file?: File) => {
        set({ isLoading: true, error: null, currentResponse: '' })

        try {
          // Add user message
          const userMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
            type: 'user',
            content: file ? `${content}\n\n[Прикреплен файл: ${file.name}]` : content,
          }
          get().appendMessage(userMessage)

          // Prepare request data
          const formData = new FormData()
          formData.append('requirements', content)

          if (file) {
            // For now, we'll just send the file name
            // TODO: Implement proper file handling
            const fileContent = await file.text()
            formData.append('file', fileContent)
          }

          // Call API
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
            }),
          })

          if (!response.ok) {
            throw new Error('Failed to generate response')
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

      clearChat: () => {
        set({ messages: [], currentResponse: '', error: null })
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