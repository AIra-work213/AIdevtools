import { vi } from 'vitest'
import '@testing-library/jest-dom'

// Provide jsdom-safe stubs for browser APIs used in components.
const localStorageMock: Storage = {
	getItem: vi.fn(),
	setItem: vi.fn(),
	removeItem: vi.fn(),
	clear: vi.fn(),
	key: vi.fn(),
	length: 0,
}

Object.defineProperty(window, 'localStorage', {
	value: localStorageMock,
	writable: true,
})

// scrollIntoView is not implemented in jsdom but is referenced by Chat page.
window.HTMLElement.prototype.scrollIntoView = vi.fn()

// matchMedia is used in ThemeProvider to detect color scheme.
Object.defineProperty(window, 'matchMedia', {
	writable: true,
	value: vi.fn().mockImplementation((query: string) => ({
		matches: false,
		media: query,
		onchange: null,
		addListener: vi.fn(),
		removeListener: vi.fn(),
		addEventListener: vi.fn(),
		removeEventListener: vi.fn(),
		dispatchEvent: vi.fn(),
	})),
})
