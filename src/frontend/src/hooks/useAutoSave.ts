import { useEffect, useRef } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { useHistoryStore } from '@/stores/historyStore'

export function useAutoSave(interval: number = 30000) { // 30 seconds
  const { messages } = useChatStore()
  const { saveChat } = useHistoryStore()
  const lastSaveRef = useRef<Date>(new Date())
  const savedMessagesCountRef = useRef(0)

  useEffect(() => {
    const timer = setInterval(() => {
      // Only save if there are new messages
      if (messages.length > savedMessagesCountRef.current && messages.length > 0) {
        // Generate title from first user message
        const firstUserMessage = messages.find(m => m.type === 'user')
        const title = firstUserMessage 
          ? firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '')
          : 'Untitled Chat'

        const lastMessage = messages[messages.length - 1]
        const metadata = lastMessage.metadata

        saveChat(title, messages, metadata)
        savedMessagesCountRef.current = messages.length
        lastSaveRef.current = new Date()
        
        console.log('Auto-saved chat with', messages.length, 'messages')
      }
    }, interval)

    return () => clearInterval(timer)
  }, [messages, saveChat, interval])

  return {
    lastSave: lastSaveRef.current,
    isSaved: savedMessagesCountRef.current === messages.length
  }
}
