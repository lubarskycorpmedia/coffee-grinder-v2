import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { PlayIcon, ClockIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface ProcessingStatus {
  state: 'idle' | 'running' | 'completed' | 'error'
  percent: number
  current_provider: string
  processed_providers: string[]
  message: string
  timestamp: string
  service_status: string
  redis_connected: boolean
  config_exists: boolean
}

const StatusDashboard = () => {
  const [isDryRun, setIsDryRun] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false)
  const queryClient = useQueryClient()
  const intervalRef = useRef<number>()
  const lastStatusRef = useRef<ProcessingStatus>()

  // Получение статуса БЕЗ автообновления
  const { data: status, isLoading, refetch } = useQuery<ProcessingStatus>(
    'processing-status',
    async () => {
      const response = await fetch('/news/api/status', {
        headers: {
          'X-API-Key': 'development_key'
        }
      })
      if (!response.ok) {
        throw new Error('Failed to fetch status')
      }
      return response.json()
    },
    {
      refetchInterval: false, // Отключаем автообновление
      refetchIntervalInBackground: false,
    }
  )

  // Функция сравнения статусов
  const hasStatusChanged = (newStatus: ProcessingStatus, oldStatus?: ProcessingStatus) => {
    if (!oldStatus) return true
    
    return (
      newStatus.state !== oldStatus.state ||
      newStatus.percent !== oldStatus.percent ||
      newStatus.current_provider !== oldStatus.current_provider ||
      newStatus.message !== oldStatus.message ||
      newStatus.processed_providers.length !== oldStatus.processed_providers.length ||
      newStatus.service_status !== oldStatus.service_status ||
      newStatus.redis_connected !== oldStatus.redis_connected ||
      newStatus.config_exists !== oldStatus.config_exists
    )
  }

  // Функция опроса статуса
  const pollStatus = async () => {
    setStatusUpdateLoading(true)
    try {
      const { data: newStatus } = await refetch()
      
      if (newStatus && hasStatusChanged(newStatus, lastStatusRef.current)) {
        lastStatusRef.current = newStatus
        
        // Если задача завершилась - останавливаем опрос
        if (newStatus.state === 'completed' || newStatus.state === 'error') {
          setIsPolling(false)
        }
      }
    } catch (error) {
      console.error('Ошибка опроса статуса:', error)
    } finally {
      setStatusUpdateLoading(false)
    }
  }

  // Управление интервалом опроса
  useEffect(() => {
    if (status) {
      lastStatusRef.current = status
      
      // Начинаем опрос только если задача запущена
      if (status.state === 'running' && !isPolling) {
        setIsPolling(true)
      }
      
      // Останавливаем опрос если задача не запущена
      if (status.state !== 'running' && isPolling) {
        setIsPolling(false)
      }
    }
  }, [status?.state])

  // Управление интервалом
  useEffect(() => {
    if (isPolling) {
      intervalRef.current = setInterval(pollStatus, 5000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isPolling])

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Мутация для запуска обработки
  const triggerMutation = useMutation(
    async () => {
      const response = await fetch('/news/api/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'development_key'
        },
        body: JSON.stringify({ dry_run: isDryRun })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to start processing')
      }
      
      return response.json()
    },
    {
      onSuccess: () => {
        toast.success('Обработка запущена!')
        queryClient.invalidateQueries('processing-status')
        // Начинаем опрос после успешного запуска
        setIsPolling(true)
      },
      onError: (error: Error) => {
        toast.error(`Ошибка запуска: ${error.message}`)
      }
    }
  )

  const getStatusColor = (state: string) => {
    switch (state) {
      case 'running':
        return 'text-coffee-cream'
      case 'completed':
        return 'text-green-400'
      case 'error':
        return 'text-red-400'
      default:
        return 'text-coffee-cream'
    }
  }

  const getStatusIcon = (state: string) => {
    switch (state) {
      case 'running':
        return <ClockIcon className="h-6 w-6 text-coffee-cream" />
      case 'completed':
        return <CheckCircleIcon className="h-6 w-6 text-green-400" />
      case 'error':
        return <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />
      default:
        return <PlayIcon className="h-6 w-6 text-coffee-cream" />
    }
  }

  const getStatusText = (state: string) => {
    switch (state) {
      case 'running':
        return 'Выполняется'
      case 'completed':
        return 'Завершено'
      case 'error':
        return 'Ошибка'
      case 'idle':
        return 'Готов к запуску'
      default:
        return 'Неизвестно'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-coffee-cream"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-coffee-cream">
            Статус обработки
          </h2>
          <div className="flex items-center space-x-2">
            {status && getStatusIcon(status.state)}
            <span className={`font-medium ${status && getStatusColor(status.state)}`}>
              {status && getStatusText(status.state)}
            </span>
            {(status?.state === 'running' || statusUpdateLoading) && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-coffee-cream opacity-70"></div>
            )}
          </div>
        </div>

        {status && (
          <div className="space-y-4">
            {/* Progress Bar */}
            {status.state === 'running' && (
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-coffee-cream">Прогресс</span>
                  <span className="text-sm font-medium text-coffee-cream">
                    {status.percent}%
                  </span>
                </div>
                <div className="w-full bg-coffee-light/30 rounded-full h-2">
                  <div 
                    className="bg-coffee-dark h-2 rounded-full transition-all duration-300"
                    style={{ width: `${status.percent}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Current Status Message */}
            <div className="bg-coffee-cream/50 rounded-lg p-3">
              <p className="text-sm text-coffee-cream">
                <strong>Сообщение:</strong> {status.message}
              </p>
              {status.current_provider && (
                <p className="text-sm text-coffee-cream mt-1">
                  <strong>Текущий провайдер:</strong> {status.current_provider}
                </p>
              )}
            </div>

            {/* Processed Providers */}
            {status.processed_providers.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-coffee-cream mb-2">
                  Обработанные провайдеры:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {status.processed_providers.map((provider) => (
                    <span 
                      key={provider}
                      className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                    >
                      {provider}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* System Status */}
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <p className="text-coffee-cream">Сервис</p>
                <p className={`font-medium ${
                  status.service_status === 'running' ? 'text-green-600' : 'text-red-400'
                }`}>
                  {status.service_status === 'running' ? 'Запущен' : 'Остановлен'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-coffee-cream">Redis</p>
                <p className={`font-medium ${
                  status.redis_connected ? 'text-green-600' : 'text-red-400'
                }`}>
                  {status.redis_connected ? 'Подключен' : 'Отключен'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-coffee-cream">Конфиг</p>
                <p className={`font-medium ${
                  status.config_exists ? 'text-green-600' : 'text-red-400'
                }`}>
                  {status.config_exists ? 'Существует' : 'Отсутствует'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Control Panel */}
      <div className="card">
        <h2 className="text-xl font-semibold text-coffee-cream mb-4">
          Управление обработкой
        </h2>

        <div className="space-y-4">
          {/* Dry Run Toggle */}
          <div className="flex items-center space-x-3">
            <input 
              type="checkbox"
              id="dry-run"
              checked={isDryRun}
              onChange={(e) => setIsDryRun(e.target.checked)}
              className="h-4 w-4 text-coffee-dark focus:ring-coffee-medium border-coffee-light rounded"
            />
            <label htmlFor="dry-run" className="text-coffee-cream">
              Режим проверки (без экспорта в Google Sheets)
            </label>
          </div>

          {/* Trigger Button */}
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={
              triggerMutation.isLoading || 
              status?.state === 'running' ||
              !status?.config_exists
            }
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {triggerMutation.isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Запуск...</span>
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4" />
                <span>Запустить обработку</span>
              </>
            )}
          </button>

          {!status?.config_exists && (
            <p className="text-red-400 text-sm text-center">
              ⚠️ Необходимо настроить конфигурацию перед запуском
            </p>
          )}
        </div>
      </div>

      {/* Last Update */}
      {status && (
        <div className="text-center text-coffee-cream text-sm">
          Последнее обновление: {new Date(status.timestamp).toLocaleString('ru-RU')}
        </div>
      )}
    </div>
  )
}

export default StatusDashboard 