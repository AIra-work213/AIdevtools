import { act, renderHook } from '@testing-library/react'
import { useHistoryStore } from '../historyStore'
import { ChatMessage } from '../chatStore'

describe('historyStore', () => {
  const mockMessages: ChatMessage[] = [
    {
      id: '1',
      type: 'user',
      content: 'Test message',
      timestamp: new Date()
    },
    {
      id: '2',
      type: 'assistant',
      content: 'Test response',
      timestamp: new Date()
    }
  ]

  beforeEach(() => {
    // Clear history before each test
    useHistoryStore.getState().clearHistory()
  })

  it('should save chat history', () => {
    const { result } = renderHook(() => useHistoryStore())

    act(() => {
      result.current.saveChat('Test Chat', mockMessages)
    })

    expect(result.current.chatHistory).toHaveLength(1)
    expect(result.current.chatHistory[0].title).toBe('Test Chat')
    expect(result.current.chatHistory[0].messages).toEqual(mockMessages)
  })

  it('should delete chat', () => {
    const { result } = renderHook(() => useHistoryStore())

    act(() => {
      const chatId = result.current.saveChat('Test Chat', mockMessages)
      result.current.deleteChat(chatId)
    })

    expect(result.current.chatHistory).toHaveLength(0)
  })

  it('should update chat title', () => {
    const { result } = renderHook(() => useHistoryStore())

    act(() => {
      const chatId = result.current.saveChat('Test Chat', mockMessages)
      result.current.updateChatTitle(chatId, 'Updated Chat')
    })

    expect(result.current.chatHistory[0].title).toBe('Updated Chat')
  })

  it('should export chat', () => {
    const { result } = renderHook(() => useHistoryStore())

    act(() => {
      result.current.saveChat('Test Chat', mockMessages)
    })

    const exportedData = result.current.exportChat(result.current.chatHistory[0].id)
    const parsed = JSON.parse(exportedData)

    expect(parsed.title).toBe('Test Chat')
    expect(parsed.messages).toHaveLength(2)
  })

  it('should load chat', () => {
    const { result } = renderHook(() => useHistoryStore())

    act(() => {
      result.current.saveChat('Test Chat', mockMessages)
    })

    const loadedChat = result.current.loadChat(result.current.chatHistory[0].id)
    expect(loadedChat?.title).toBe('Test Chat')
    expect(loadedChat?.messages).toEqual(mockMessages)
  })
})