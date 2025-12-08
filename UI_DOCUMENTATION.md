# 🎨 TestOps Copilot - UI/UX Документация

## Визуальная структура приложения

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER WINDOW                           │
│  http://localhost:3001                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┬──────────────────────────────────────────┐ │
│  │                │  🌓 Theme Toggle    👤 User Menu         │ │
│  │   SIDEBAR      │                                          │ │
│  │   (lg:w-64)    ├──────────────────────────────────────────┤ │
│  │                │                                          │ │
│  │ 📊 Дашборд     │         MAIN CONTENT AREA               │ │
│  │ 💬 Чат         │                                          │ │
│  │ 🕐 История     │   ┌──────────────┬─────────────────┐    │ │
│  │ ⚙️ Настройки   │   │              │                 │    │ │
│  │                │   │  CHAT AREA   │  CODE EDITOR    │    │ │
│  │                │   │              │                 │    │ │
│  │  [Logo]        │   │  Messages:   │  Generated:     │    │ │
│  │  TestOps       │   │  • User      │  • Python code  │    │ │
│  │  Copilot       │   │  • AI        │  • Pytest tests │    │ │
│  │                │   │              │  • Allure       │    │ │
│  │                │   ├──────────────┴─────────────────┤    │ │
│  │                │   │  Input + File Upload           │    │ │
│  │                │   │  [Type message...] 📎 ✈️       │    │ │
│  └────────────────┘   └────────────────────────────────┘    │ │
│                                                              │ │
└──────────────────────────────────────────────────────────────┘ │
```

## Цветовая палитра

### Light Theme
```
Background: radial-gradient(
  circle at 20% 20%,
  #e0f2fe (sky-200) 0%,
  #eef2ff (indigo-50) 35%,
  #f8fafc (slate-50) 70%,
  #e2e8f0 (slate-200) 100%
)

Cards: rgba(255, 255, 255, 0.7) + backdrop-blur
Borders: rgba(255, 255, 255, 0.2)
Text: #0f172a (slate-900)
Primary: #3b82f6 (blue-500)
```

### Dark Theme
```
Background: radial-gradient(
  circle at 15% 20%,
  #312e81 (violet-900) 0%,
  #0f172a (slate-900) 45%,
  #020617 (slate-950) 100%
)

Cards: rgba(255, 255, 255, 0.05) + backdrop-blur
Borders: rgba(255, 255, 255, 0.1)
Text: #e2e8f0 (slate-200)
Primary: #60a5fa (blue-400)
```

## Компоненты UI

### 1. Sidebar Navigation
```tsx
// Desktop: fixed, w-64
// Mobile: overlay с backdrop

Features:
- Logo component (gradient SVG)
- Navigation items с icons (Heroicons)
- Active state highlighting
- Smooth transitions
- Glassmorphism effect
```

### 2. Chat Interface
```tsx
Features:
- Message bubbles (user/assistant)
- File upload с drag & drop
- Auto-scroll на новые сообщения
- Loading states
- Error toast notifications
- Settings panel toggle
```

### 3. Code Editor
```tsx
Features:
- Syntax highlighting (Monaco/Prism)
- Copy to clipboard
- Line numbers
- Readonly mode
- Language detection
```

### 4. Buttons
```css
.btn-primary
  - Gradient: primary → fuchsia
  - Shadow: primary-500/30
  - Hover: darker gradient
  - Focus ring: primary-400

.btn-secondary
  - White/70 background
  - Dark: white/10
  - Subtle shadow

.btn-ghost
  - Transparent background
  - Hover: white/60
```

### 5. Inputs
```css
.input
  - White/70 background
  - Border: white/20
  - Focus: primary-500 ring
  - Placeholder: gray-400
  - Dark mode: white/5 bg
```

## Анимации

```css
@keyframes fadeIn {
  0%   { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes slideUp {
  0%   { transform: translateY(10px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

.animate-pulse-slow {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

## Адаптивность

### Breakpoints (TailwindCSS)
```
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
2xl: 1536px
```

### Mobile (< 1024px)
- Hamburger menu
- Overlay sidebar
- Stacked layout
- Touch-friendly buttons

### Desktop (≥ 1024px)
- Fixed sidebar
- Split layout (chat + editor)
- Hover effects
- Keyboard shortcuts

## Типографика

### Fonts
```css
Sans: 'Inter', system-ui, sans-serif
Mono: 'JetBrains Mono', 'Consolas', monospace
```

### Text Sizes
```
Heading 1: text-3xl font-bold
Heading 2: text-xl font-semibold
Body:      text-sm
Small:     text-xs
Code:      font-mono text-sm
```

## Accessibility

✅ **WCAG 2.1 AA Compliance**
- Color contrast ratios > 4.5:1
- Keyboard navigation
- ARIA labels
- Focus indicators
- Screen reader support

✅ **Semantic HTML**
- Proper heading hierarchy
- Button vs link usage
- Form labels
- Alt text для images

✅ **Focus Management**
- Visible focus rings
- Logical tab order
- Skip links (optional)

## Иконки (Heroicons)

```tsx
Chat:         ChatBubbleLeftRightIcon
Dashboard:    Squares2X2Icon
History:      ClockIcon
Settings:     Cog6ToothIcon
Sun:          SunIcon (light mode)
Moon:         MoonIcon (dark mode)
Menu:         Bars3Icon (mobile)
Close:        XMarkIcon
Send:         PaperAirplaneIcon
File:         DocumentIcon
```

## Loading States

### Spinner
```tsx
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
```

### Skeleton
```tsx
<div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded" />
```

### Progress
```tsx
<div className="w-full bg-gray-200 rounded-full h-2">
  <div className="bg-primary-500 h-2 rounded-full animate-pulse" />
</div>
```

## Декоративные элементы

### Gradient Orbs
```tsx
{/* Top left */}
<div className="absolute -top-24 -left-32 h-80 w-80 
     rounded-full bg-primary-400/30 blur-3xl" />

{/* Top right */}
<div className="absolute top-10 right-[-6rem] h-96 w-96 
     rounded-full bg-fuchsia-400/25 blur-3xl" />
```

### Glassmorphism Card
```css
background: rgba(255, 255, 255, 0.7);
backdrop-filter: blur(10px);
border: 1px solid rgba(255, 255, 255, 0.2);
box-shadow: 0 25px 50px -12px rgba(59, 130, 246, 0.1);
```

## Примеры использования

### Chat Message (User)
```tsx
<div className="chat-message user">
  <p className="text-sm">Создай тесты для функции</p>
</div>

// Compiled:
background: #eff6ff (primary-50)
margin-left: 2rem
padding: 0.75rem 1rem
border-radius: 0.5rem
```

### Chat Message (Assistant)
```tsx
<div className="chat-message assistant">
  <p className="text-sm">Вот сгенерированные тесты...</p>
</div>

// Compiled:
background: #f3f4f6 (gray-100)
margin-right: 2rem
padding: 0.75rem 1rem
border-radius: 0.5rem
```

---

## 🎯 Design Principles

1. **Clarity** - Чистый интерфейс без визуального шума
2. **Consistency** - Единая дизайн-система
3. **Feedback** - Немедленная реакция на действия
4. **Accessibility** - Доступно для всех
5. **Performance** - Быстрые анимации, оптимизированные стили
6. **Aesthetics** - Современный градиентный дизайн

---

**Создано с использованием TailwindCSS 3 + React 18**
