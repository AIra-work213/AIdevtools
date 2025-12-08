import { Mock, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Chat } from '../../pages/Chat'
import { useChatStore } from '../../stores/chatStore'

vi.mock('../../stores/chatStore', () => ({
  useChatStore: vi.fn(),
}))

vi.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value }: { value: string }) => (
    <textarea data-testid="code-editor" value={value} readOnly />
  ),
}))

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

type MockStore = {
  messages: Array<{ id: string; type: string; content: string; timestamp: Date }>
  isLoading: boolean
  error: string | null
  currentResponse: string
  sendMessage: ReturnType<typeof vi.fn>
  clearChat: ReturnType<typeof vi.fn>
}

const createStore = (overrides: Partial<MockStore> = {}): MockStore => ({
  messages: [],
  isLoading: false,
  error: null,
  currentResponse: '',
  sendMessage: vi.fn().mockResolvedValue(undefined),
  clearChat: vi.fn(),
  ...overrides,
})

const mockUseChatStore = useChatStore as unknown as Mock

beforeEach(() => {
  vi.clearAllMocks()
  mockUseChatStore.mockReturnValue(createStore())
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
    const user = userEvent
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
    const user = userEvent
    renderWithProviders(<Chat />)

    const sendButton = screen.getByRole('button', { name: /отправить/i })
    await user.click(sendButton)

    expect(await screen.findByText('Сообщение не может быть пустым')).toBeInTheDocument()
  })

  test('handles file upload', async () => {
    const user = userEvent
    renderWithProviders(<Chat />)

    const fileInput = screen.getByTitle('Прикрепить файл')
    const file = new File(['test content'], 'test.py', { type: 'text/plain' })

    await user.upload(fileInput, file)

    expect(screen.getByText('test.py')).toBeInTheDocument()
  })

  test('clears file selection', async () => {
    const user = userEvent
    renderWithProviders(<Chat />)

    const fileInput = screen.getByTitle('Прикрепить файл')
    const file = new File(['test content'], 'test.py', { type: 'text/plain' })

    await user.upload(fileInput, file)
    await user.click(screen.getByText('×'))

    expect(screen.queryByText('test.py')).not.toBeInTheDocument()
  })

  test('opens settings panel', async () => {
    const user = userEvent
    renderWithProviders(<Chat />)

    const settingsButton = screen.getByTitle('Настройки генерации')
    await user.click(settingsButton)

    expect(screen.getByText('Настройки генерации')).toBeInTheDocument()
    expect(screen.getByText('Тип тестов')).toBeInTheDocument()
  })

  test('clears chat history', async () => {
    const mockClearChat = vi.fn()
    mockUseChatStore.mockReturnValue(createStore({
      messages: [
        { id: '1', type: 'user', content: 'Test message', timestamp: new Date() },
      ],
      clearChat: mockClearChat,
    }))

    const user = userEvent
    renderWithProviders(<Chat />)

    const clearButton = screen.getByText('Очистить')
    await user.click(clearButton)

    expect(mockClearChat).toHaveBeenCalled()
  })
})