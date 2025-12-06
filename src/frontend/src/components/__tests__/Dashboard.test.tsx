import type { ReactElement } from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Dashboard } from '../../pages/Dashboard'

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const renderWithProviders = (ui: ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Dashboard', () => {
  test('renders welcome message', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Добро пожаловать в TestOps Copilot!')).toBeInTheDocument()
    expect(
      screen.getByText('Интеллектуальный ассистент для автоматизации QA процессов')
    ).toBeInTheDocument()
  })

  test('renders metrics cards', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Сгенерировано тестов')).toBeInTheDocument()
    expect(screen.getByText('Валидаций кода')).toBeInTheDocument()
    expect(screen.getByText('Активных чатов')).toBeInTheDocument()
    expect(screen.getByText('Сохранено в GitLab')).toBeInTheDocument()
  })

  test('renders quick actions', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Быстрые действия')).toBeInTheDocument()
    expect(screen.getByText('Генерация ручных тестов')).toBeInTheDocument()
    expect(screen.getByText('Генерация API тестов')).toBeInTheDocument()
    expect(screen.getByText('Валидация кода')).toBeInTheDocument()
    expect(screen.getByText('Поиск дубликатов')).toBeInTheDocument()
  })

  test('renders recent activity', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Последняя активность')).toBeInTheDocument()
  })

  test('renders CTA section', () => {
    renderWithProviders(<Dashboard />)

    expect(
      screen.getByText('Начните генерировать тесты прямо сейчас')
    ).toBeInTheDocument()
    expect(screen.getByText('Открыть чат')).toBeInTheDocument()
  })
})