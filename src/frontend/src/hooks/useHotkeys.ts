import { useEffect } from 'react'

interface HotkeyConfig {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  callback: () => void
}

export function useHotkeys(hotkeys: HotkeyConfig[]) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      for (const hotkey of hotkeys) {
        const ctrlMatch = hotkey.ctrl === undefined || hotkey.ctrl === event.ctrlKey || hotkey.ctrl === event.metaKey
        const shiftMatch = hotkey.shift === undefined || hotkey.shift === event.shiftKey
        const altMatch = hotkey.alt === undefined || hotkey.alt === event.altKey
        const keyMatch = hotkey.key.toLowerCase() === event.key.toLowerCase()

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          event.preventDefault()
          hotkey.callback()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [hotkeys])
}
