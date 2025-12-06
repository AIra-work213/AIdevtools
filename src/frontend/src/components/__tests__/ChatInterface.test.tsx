import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Chat } from '../../pages/Chat'

// Mock zustand store
jest.mock('../../stores/chatStore', () => ({
  useChatStore: () => ({
    messages: [],
    isLoading: false,
    error: null,
    currentResponse: '',
    sendMessage: jest.fn().mockResolvedValue(undefined),
    clearChat: jest.fn(),
  }),
}))

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => {
  return function MockEditor({ value }: { value: string }) {
    return <textarea data-testid="code-editor" value={value} readOnly />
  }
})

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const renderWithProviders = (ui: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Chat Page', () => {
  test('renders chat interface', () => {
    renderWithProviders(<Chat />)

    expect(screen.getByPlaceholderText('Введите требования или описание теста...')).toBeInTheDocument()
    expect(screen.getByText('Чат с ассистентом')).toBeInTheDocument()
  })

  test('sends message on form submit', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Chat />)

    const input = screen.getByPlaceholderText('Введите требования или описание теста...')
    const sendButton = screen.getByRole('button', { name: /отправить/i })

    await user.type(input, 'Generate tests for login')
    await user.click(sendButton)

    await waitFor(() => {
      expect(input).toHaveValue('')
    })
  })

  test('validates empty message', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Chat />)

    const sendButton = screen.getByRole('button', { name: /отправить/i })
    await user.click(sendButton)

    // Should show validation error
    expect(screen.getByText('Сообщение не может быть пустым')).toBeInTheDocument()
  })

  test('handles file upload', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Chat />)

    const fileInput = screen.getByTitle('Прикрепить файл')
    const file = new File(['test content'], 'test.py', { type: 'text/plain' })

    await user.upload(fileInput, file)

    // Should display file name
    expect(screen.getByText('test.py')).toBeInTheDocument()
  })

  test('clears file selection', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Chat />)

    const fileInput = screen.getByTitle('Прикрепить файл')
    const file = new File(['test content'], 'test.py', { type: 'text/plain' })

    await user.upload(fileInput, file)
    await user.click(screen.getByText('×'))

    // File should be removed
    expect(screen.queryByText('test.py')).not.toBeInTheDocument()
  })

  test('opens settings panel', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Chat />)

    const settingsButton = screen.getByTitle('Настройки генерации')
    await user.click(settingsButton)

    expect(screen.getByText('Настройки генерации')).toBeInTheDocument()
    expect(screen.getByText('Тип тестов')).toBeInTheDocument()
  })

  test('clears chat history', async () => {
    const mockClearChat = jest.fn()
    jest.doMock('../../stores/chatStore', () => ({
      useChatStore: () => ({
        messages: [
          { id: '1', type: 'user', content: 'Test message', timestamp: new Date() }
        ],
        isLoading: false,
        error: null,
        currentResponse: '',
        sendMessage: jest.fn(),
        clearChat: mockClearChat,
      }),
    }))

    const user = userEvent.setup()
    renderWithProviders(<Chat />)

    const clearButton = screen.getByText('Очистить')
    await user.click(clearButton)

    expect(mockClearChat).toHaveBeenCalled()
  })
})