import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Chat } from '@/pages/Chat'
import { History } from '@/pages/History'
import { Settings } from '@/pages/Settings'
import { Validate } from '@/pages/Validate'
import { Duplicates } from '@/pages/Duplicates'
import { ApiTests } from '@/pages/ApiTests'
import { UiTests } from '@/pages/UiTests'
import { CodeRunner } from '@/pages/CodeRunner'
import Coverage from '@/pages/Coverage'
import { ProtectedRoute } from '@/components/ProtectedRoute'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />
        <Route
          path="/coverage"
          element={
            <ProtectedRoute>
              <Coverage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/validate"
          element={
            <ProtectedRoute>
              <Validate />
            </ProtectedRoute>
          }
        />
        <Route
          path="/duplicates"
          element={
            <ProtectedRoute>
              <Duplicates />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-tests"
          element={
            <ProtectedRoute>
              <ApiTests />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ui-tests"
          element={
            <ProtectedRoute>
              <UiTests />
            </ProtectedRoute>
          }
        />
        <Route
          path="/run"
          element={
            <ProtectedRoute>
              <CodeRunner />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

export default App