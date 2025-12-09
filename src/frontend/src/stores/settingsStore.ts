import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface GenerationSettings {
  test_type: string
  detail_level: 'minimal' | 'standard' | 'detailed'
  use_aaa_pattern: boolean
  include_negative_tests: boolean
  temperature: number
  max_tokens: number
  language: string
  framework: string
}

interface SettingsState {
  generationSettings: GenerationSettings

  // Actions
  updateSettings: (settings: Partial<GenerationSettings>) => void
  resetSettings: () => void
}

const defaultSettings: GenerationSettings = {
  test_type: 'manual',
  detail_level: 'standard',
  use_aaa_pattern: true,
  include_negative_tests: true,
  temperature: 0.3,
  max_tokens: 16000,
  language: 'python',
  framework: 'pytest'
}

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set) => ({
        generationSettings: defaultSettings,

        updateSettings: (newSettings) =>
          set((state) => ({
            generationSettings: {
              ...state.generationSettings,
              ...newSettings,
            },
          })),

        resetSettings: () =>
          set({
            generationSettings: defaultSettings,
          }),
      }),
      {
        name: 'generation-settings',
        partialize: (state) => ({ generationSettings: state.generationSettings }),
      }
    ),
    {
      name: 'settings-store',
    }
  )
)