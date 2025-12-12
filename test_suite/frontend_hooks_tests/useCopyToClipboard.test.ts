import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useCopyToClipboard } from '../useCopyToClipboard'

// Mock toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Mock navigator.clipboard
const mockWriteText = vi.fn()

Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText,
  },
})

describe('useCopyToClipboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should copy text to clipboard', async () => {
    mockWriteText.mockResolvedValueOnce(undefined)
    
    const { result } = renderHook(() => useCopyToClipboard())
    
    const success = await result.current.copyToClipboard('test text')
    
    expect(success).toBe(true)
    expect(mockWriteText).toHaveBeenCalledWith('test text')
    
    await waitFor(() => {
      expect(result.current.copiedText).toBe('test text')
    })
  })

  it('should handle copy failure', async () => {
    mockWriteText.mockRejectedValueOnce(new Error('Failed'))
    
    const { result } = renderHook(() => useCopyToClipboard())
    
    const success = await result.current.copyToClipboard('test text')
    
    expect(success).toBe(false)
    expect(result.current.copiedText).toBe(null)
  })

  it('should reset copied text after timeout', async () => {
    vi.useFakeTimers()
    mockWriteText.mockResolvedValueOnce(undefined)
    
    const { result } = renderHook(() => useCopyToClipboard())
    
    await result.current.copyToClipboard('test text')
    
    await waitFor(() => {
      expect(result.current.copiedText).toBe('test text')
    })
    
    vi.advanceTimersByTime(2000)
    
    await waitFor(() => {
      expect(result.current.copiedText).toBe(null)
    })
    
    vi.useRealTimers()
  })
})
