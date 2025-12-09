import { useState } from 'react'
import { toast } from 'react-hot-toast'

export function useCopyToClipboard() {
  const [copiedText, setCopiedText] = useState<string | null>(null)

  const copyToClipboard = async (text: string, successMessage = 'Скопировано в буфер обмена') => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedText(text)
      toast.success(successMessage)
      
      // Reset after 2 seconds
      setTimeout(() => setCopiedText(null), 2000)
      
      return true
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
      toast.error('Не удалось скопировать')
      return false
    }
  }

  return { copiedText, copyToClipboard }
}
