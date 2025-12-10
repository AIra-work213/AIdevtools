import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  ChatBubbleLeftRightIcon,
  Squares2X2Icon,
  ClockIcon,
  Cog6ToothIcon,
  SunIcon,
  MoonIcon,
  Bars3Icon,
  XMarkIcon,
  ChartBarIcon,
  CodeBracketIcon,
  CursorArrowRaysIcon,
  PlayIcon,
} from '@heroicons/react/24/outline'
import { useTheme } from '@/contexts/ThemeContext'
import { Logo } from '@/components/ui/Logo'
import { UserMenu } from '@/components/ui/UserMenu'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()

  const navigation = [
    { name: 'Дашборд', href: '/dashboard', icon: Squares2X2Icon },
    { name: 'Чат с ассистентом', href: '/chat', icon: ChatBubbleLeftRightIcon },
    { name: 'История', href: '/history', icon: ClockIcon },
    { name: 'Покрытие кода', href: '/coverage', icon: ChartBarIcon },
    { name: 'API тесты', href: '/api-tests', icon: CodeBracketIcon },
    { name: 'UI тесты', href: '/ui-tests', icon: CursorArrowRaysIcon },
    { name: 'Запуск тестов', href: '/run', icon: PlayIcon },
    { name: 'Настройки', href: '/settings', icon: Cog6ToothIcon },
  ]

  return (
    <div className="relative min-h-screen text-slate-900 dark:text-slate-100">
      {/* Decorative gradients */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 -left-32 h-80 w-80 rounded-full bg-primary-400/30 blur-3xl" aria-hidden="true" />
        <div className="absolute top-10 right-[-6rem] h-96 w-96 rounded-full bg-fuchsia-400/25 blur-3xl" aria-hidden="true" />
      </div>
      {/* Mobile sidebar */}
      <div className={`lg:hidden fixed inset-0 z-50 ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-slate-950/70" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col border-r border-white/10 bg-white/90 backdrop-blur dark:bg-slate-900/80">
          <div className="flex h-16 items-center justify-between px-4">
            <Logo />
            <button
              type="button"
              className="-m-2.5 p-2.5 text-gray-700 dark:text-gray-200"
              onClick={() => setSidebarOpen(false)}
            >
              <span className="sr-only">Закрыть меню</span>
              <XMarkIcon className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-4 py-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                        : 'text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-gray-700'
                    }`
                  }
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 flex-shrink-0 ${
                      isActive
                        ? 'text-primary-500 dark:text-primary-400'
                        : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </NavLink>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-grow flex-col overflow-y-auto border-r border-white/10 bg-white/80 backdrop-blur dark:bg-slate-900/80 transition-theme">
          <div className="flex h-16 items-center px-6">
            <Logo />
          </div>
          <nav className="flex-1 space-y-1 px-4 py-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                        : 'text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-gray-700'
                    }`
                  }
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 flex-shrink-0 transition-colors duration-200 ${
                      isActive
                        ? 'text-primary-500 dark:text-primary-400'
                        : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </NavLink>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64 relative">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-white/10 bg-white/70 px-4 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-900/70 sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Открыть меню</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1" />
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              {/* Theme toggle */}
              <button
                type="button"
                className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                onClick={toggleTheme}
              >
                <span className="sr-only">Переключить тему</span>
                {theme === 'dark' ? (
                  <SunIcon className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <MoonIcon className="h-5 w-5" aria-hidden="true" />
                )}
              </button>

              <UserMenu />
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  )
}