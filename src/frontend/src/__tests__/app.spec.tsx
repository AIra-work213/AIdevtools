import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import App from '@/App'
import { ThemeProvider } from '@/contexts/ThemeContext'

const renderApp = () => {
  const queryClient = new QueryClient()

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('App shell', () => {
  it('renders dashboard title', () => {
    renderApp()
    expect(screen.getByText(/Добро пожаловать в TestOps Copilot/i)).toBeInTheDocument()
  })

  it('renders navigation links once each', () => {
    renderApp()

    const links = [
      'Дашборд',
      'Чат с ассистентом',
      'История',
      'Настройки',
    ]

    links.forEach((label) => {
      const elements = screen.getAllByText(label)
      expect(elements.length).toBeGreaterThan(0)
    })
  })
})
