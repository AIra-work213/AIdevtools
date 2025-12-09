import { act, renderHook } from '@testing-library/react'
import { useSettingsStore } from '../settingsStore'

describe('settingsStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useSettingsStore.getState().resetSettings()
  })

  it('should have default settings', () => {
    const { result } = renderHook(() => useSettingsStore())

    expect(result.current.generationSettings).toEqual({
      test_type: 'manual',
      detail_level: 'standard',
      use_aaa_pattern: true,
      include_negative_tests: true,
      temperature: 0.3,
      max_tokens: 16000,
      language: 'python',
      framework: 'pytest'
    })
  })

  it('should update settings', () => {
    const { result } = renderHook(() => useSettingsStore())

    act(() => {
      result.current.updateSettings({
        temperature: 0.7,
        detail_level: 'detailed'
      })
    })

    expect(result.current.generationSettings.temperature).toBe(0.7)
    expect(result.current.generationSettings.detail_level).toBe('detailed')
  })

  it('should reset settings to defaults', () => {
    const { result } = renderHook(() => useSettingsStore())

    act(() => {
      result.current.updateSettings({
        temperature: 1.0,
        language: 'javascript'
      })
    })

    expect(result.current.generationSettings.temperature).toBe(1.0)
    expect(result.current.generationSettings.language).toBe('javascript')

    act(() => {
      result.current.resetSettings()
    })

    expect(result.current.generationSettings.temperature).toBe(0.3)
    expect(result.current.generationSettings.language).toBe('python')
  })
})