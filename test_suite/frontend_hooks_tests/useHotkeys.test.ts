import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { useHotkeys } from '../useHotkeys'

describe('useHotkeys', () => {
  it('should call callback on matching hotkey', () => {
    const callback = vi.fn()
    
    renderHook(() => 
      useHotkeys([
        {
          key: 's',
          ctrl: true,
          callback,
        },
      ])
    )
    
    act(() => {
      const event = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
      })
      window.dispatchEvent(event)
    })
    
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('should handle multiple hotkeys', () => {
    const callback1 = vi.fn()
    const callback2 = vi.fn()
    
    renderHook(() =>
      useHotkeys([
        {
          key: 's',
          ctrl: true,
          callback: callback1,
        },
        {
          key: 'k',
          ctrl: true,
          callback: callback2,
        },
      ])
    )
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))
    })
    
    expect(callback1).toHaveBeenCalledTimes(1)
    expect(callback2).toHaveBeenCalledTimes(1)
  })

  it('should not call callback on non-matching hotkey', () => {
    const callback = vi.fn()
    
    renderHook(() =>
      useHotkeys([
        {
          key: 's',
          ctrl: true,
          callback,
        },
      ])
    )
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's' })) // Missing ctrl
    })
    
    expect(callback).not.toHaveBeenCalled()
  })

  it('should handle shift and alt modifiers', () => {
    const callback = vi.fn()
    
    renderHook(() =>
      useHotkeys([
        {
          key: 'c',
          ctrl: true,
          shift: true,
          callback,
        },
      ])
    )
    
    act(() => {
      window.dispatchEvent(
        new KeyboardEvent('keydown', {
          key: 'c',
          ctrlKey: true,
          shiftKey: true,
        })
      )
    })
    
    expect(callback).toHaveBeenCalledTimes(1)
  })
})
