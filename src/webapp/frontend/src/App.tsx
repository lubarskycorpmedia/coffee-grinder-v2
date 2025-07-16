import { useState } from 'react'
import ConfigEditor from './components/ConfigEditor'
import StatusDashboard from './components/StatusDashboard'

function App() {
  const [activeTab, setActiveTab] = useState<'config' | 'status'>('status')

  return (
    <div className="min-h-screen coffee-gradient-accent">
      {/* Header */}
      <header className="coffee-gradient-accent shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-coffee-foam">
                  ☕ Coffee Grinder v2
                </h1>
              </div>
              <div className="ml-10">
                <p className="text-coffee-cream text-sm">
                  Система управления новостями
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-coffee-dark shadow-lg border-b border-coffee-medium/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('status')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200 ${
                activeTab === 'status'
                  ? 'border-coffee-cream text-coffee-cream'
                  : 'border-transparent text-coffee-cream hover:text-coffee-cream hover:border-coffee-light'
              }`}
            >
              📊 Статус и запуск
            </button>
            <button
              onClick={() => setActiveTab('config')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200 ${
                activeTab === 'config'
                  ? 'border-coffee-cream text-coffee-cream'
                  : 'border-transparent text-coffee-cream hover:text-coffee-cream hover:border-coffee-light'
              }`}
            >
              ⚙️ Конфигурация
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {activeTab === 'status' && <StatusDashboard />}
        {activeTab === 'config' && <ConfigEditor />}
      </main>

      {/* Footer */}
      <footer className="bg-coffee-dark border-t border-coffee-medium/30 mt-12">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-coffee-cream text-sm">
            Coffee Grinder v2 - AI-powered news processing system
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App 