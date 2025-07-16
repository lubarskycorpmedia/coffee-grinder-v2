import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { PlayIcon, ClockIcon, CheckCircleIcon, ExclamationTriangleIcon, DocumentTextIcon, XMarkIcon } from '@heroicons/react/24/outline'

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
  start_time?: string
  end_time?: string
  duration?: number
}

interface LogEntry {
  timestamp: string
  level: string
  method: string
  message: string
  rawLine: string
}

interface LogsResponse {
  success: boolean
  lines_requested: number
  lines_returned: number
  log_file: string | null
  logs: string[]
  timestamp: string
}

const StatusDashboard = () => {
  const [isDryRun, setIsDryRun] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false)
  
  // Состояния для логов
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [logFilter, setLogFilter] = useState<string>('ALL') // ALL, INFO, ERROR, DEBUG, WARNING
  const [isLoadingLogs, setIsLoadingLogs] = useState(false)
  
  const queryClient = useQueryClient()
  const intervalRef = useRef<number>()
  const lastStatusRef = useRef<ProcessingStatus>()
  const logsContainerRef = useRef<HTMLDivElement>(null)

  // Функция парсинга лога
  const parseLogLine = (line: string): LogEntry => {
    // Реальный формат логов контейнера: "2025-07-16 11:45:32 - src.services.news.pipeline - INFO - message"
    const containerFormat = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*([^-]+)\s*-\s*(\w+)\s*-\s*(.+)$/
    
    // Старый формат с миллисекундами: "2024-01-15 10:30:45,123 - coffee_grinder - INFO - message"
    const oldFormat = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-\s*([^-]+)\s*-\s*(\w+)\s*-\s*(.+)$/
    
    // Простой формат "LEVEL: message"
    const simpleFormat = /^(\w+):\s*(.+)$/
    
    let match = line.match(containerFormat)
    if (match) {
      const [, timestamp, module, level, message] = match
      return {
        timestamp: timestamp.trim(),
        level: level.trim(),
        method: module.trim(),
        message: message.trim(),
        rawLine: line
      }
    }
    
    match = line.match(oldFormat)
    if (match) {
      const [, timestamp, module, level, message] = match
      return {
        timestamp: timestamp.trim(),
        level: level.trim(),
        method: module.trim(),
        message: message.trim(),
        rawLine: line
      }
    }
    
    match = line.match(simpleFormat)
    if (match) {
      const [, level, message] = match
      return {
        timestamp: new Date().toISOString().slice(11, 19),
        level: level.trim(),
        method: 'system',
        message: message.trim(),
        rawLine: line
      }
    }
    
    // Если не удалось распарсить, возвращаем как есть
    return {
      timestamp: new Date().toISOString().slice(11, 19),
      level: 'INFO',
      method: 'system',
      message: line.trim(),
      rawLine: line
    }
  }

  // Функция получения логов
  const fetchLogs = async () => {
    setIsLoadingLogs(true)
    try {
      const response = await fetch('/news/api/logs?lines=200', {
        headers: {
          'X-API-Key': 'development_key'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch logs')
      }
      
      const data: LogsResponse = await response.json()
      
      if (data.success && data.logs) {
        // Сначала покажем ВСЕ логи для отладки
        const parsedLogs = data.logs.map(parseLogLine)
        
        console.log('Получено логов:', data.logs.length)
        console.log('Пример первых 3 строк:', data.logs.slice(0, 3))
        
        setLogs(parsedLogs)
      }
    } catch (error) {
      console.error('Ошибка получения логов:', error)
      toast.error('Ошибка загрузки логов')
    } finally {
      setIsLoadingLogs(false)
    }
  }

  // Фильтрация логов
  useEffect(() => {
    if (logFilter === 'ALL') {
      setFilteredLogs(logs)
    } else {
      setFilteredLogs(logs.filter((log: LogEntry) => log.level === logFilter))
    }
  }, [logs, logFilter])

  // Автопрокрутка к новым логам
  useEffect(() => {
    if (logsContainerRef.current && showLogsModal) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
    }
  }, [filteredLogs, showLogsModal])

  // Очистка логов
  const clearLogs = () => {
    setLogs([])
    setFilteredLogs([])
  }

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

      // Обновляем логи если модальное окно открыто и процесс запущен
      if (showLogsModal && newStatus?.state === 'running') {
        await fetchLogs()
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
        return 'text-coffee-cream'
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
        return <CheckCircleIcon className="h-6 w-6 text-coffee-cream" />
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

  // Функция для получения информации о времени статуса
  const getStatusTimeInfo = (status: ProcessingStatus): { timeString: string; label: string } | null => {
    const formatTime = (timeString: string): string => {
      const date = new Date(timeString)
      const day = date.getDate().toString().padStart(2, '0')
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const year = date.getFullYear()
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      const seconds = date.getSeconds().toString().padStart(2, '0')
      return `${day}.${month}.${year}, ${hours}:${minutes}:${seconds}`
    }

    switch (status.state) {
      case 'running':
        if (status.start_time) {
          return {
            timeString: formatTime(status.start_time),
            label: 'Время начала:'
          }
        }
        break
      
      case 'completed':
        if (status.end_time) {
          return {
            timeString: formatTime(status.end_time),
            label: 'Время завершения:'
          }
        }
        break
      
      case 'error':
        if (status.end_time) {
          return {
            timeString: formatTime(status.end_time),
            label: 'Время ошибки:'
          }
        }
        break
      
      case 'idle':
        if (status.end_time) {
          return {
            timeString: formatTime(status.end_time),
            label: 'Последнее завершение:'
          }
        } else if (status.timestamp) {
          return {
            timeString: formatTime(status.timestamp),
            label: 'Последнее обновление:'
          }
        }
        break
    }

    return null
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
                {(() => {
                  const timeInfo = getStatusTimeInfo(status)
                  if (timeInfo) {
                    return ` (${timeInfo.label} ${timeInfo.timeString})`
                  }
                  return ''
                })()}
              </p>
              {status.current_provider && (
                <p className="text-sm text-coffee-cream mt-1">
                  <strong>Текущий провайдер:</strong> {status.current_provider}
                </p>
              )}
              {status.state === 'completed' && status.duration && (
                <div className="mt-2">
                  <p className="text-sm text-coffee-cream">
                    <strong>Длительность:</strong> {(() => {
                      const totalSeconds = Math.round(status.duration!)
                      const hours = Math.floor(totalSeconds / 3600)
                      const minutes = Math.floor((totalSeconds % 3600) / 60)
                      const seconds = totalSeconds % 60
                      
                      if (hours > 0) {
                        return `${hours} час ${minutes} мин ${seconds} сек`
                      } else if (minutes > 0) {
                        return `${minutes} мин ${seconds} сек`
                      } else {
                        return `${seconds} сек`
                      }
                    })()}
                  </p>
                </div>
              )}
            </div>

            {/* Processed Providers */}
            {status.processed_providers.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold text-coffee-cream">
                  Обработанные провайдеры:
                </span>
                {status.processed_providers.map((provider) => (
                  <span 
                    key={provider}
                    className="px-2 py-1 bg-coffee-light text-coffee-foam text-xs rounded-full"
                  >
                    {provider}
                  </span>
                ))}
              </div>
            )}

            {/* System Status */}
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <p className="text-coffee-cream">Сервис</p>
                <p className={`font-medium ${
                  status.service_status === 'running' ? 'text-coffee-cream' : 'text-red-400'
                }`}>
                  {status.service_status === 'running' ? 'Запущен' : 'Остановлен'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-coffee-cream">Redis</p>
                <p className={`font-medium ${
                  status.redis_connected ? 'text-coffee-cream' : 'text-red-400'
                }`}>
                  {status.redis_connected ? 'Подключен' : 'Отключен'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-coffee-cream">Конфиг</p>
                <p className={`font-medium ${
                  status.config_exists ? 'text-coffee-cream' : 'text-red-400'
                }`}>
                  {status.config_exists ? 'Существует' : 'Отсутствует'}
                </p>
              </div>
              <div className="flex justify-center items-center">
                <button
                  onClick={() => {
                    setShowLogsModal(true)
                    fetchLogs()
                  }}
                  className="btn-secondary flex items-center justify-center space-x-2 px-4 py-2"
                  title="Просмотр логов обработки"
                >
                  <DocumentTextIcon className="h-4 w-4" />
                  <span>Логи</span>
                </button>
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

      {/* Logs Modal */}
      {showLogsModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowLogsModal(false)}
        >
          <div 
            className="bg-coffee-light rounded-lg shadow-xl w-full max-w-6xl h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-coffee-medium">
              <div className="flex items-center space-x-3">
                <DocumentTextIcon className="h-6 w-6 text-coffee-cream" />
                <h2 className="text-xl font-semibold text-coffee-cream">
                  Логи обработки новостей
                </h2>
                {isLoadingLogs && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-coffee-cream"></div>
                )}
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Log Level Filter */}
                <select
                  value={logFilter}
                  onChange={(e) => setLogFilter(e.target.value)}
                  className="bg-coffee-medium text-coffee-cream border border-coffee-dark rounded px-3 py-1 text-sm"
                >
                  <option value="ALL">Все уровни</option>
                  <option value="INFO">INFO</option>
                  <option value="ERROR">ERROR</option>
                  <option value="DEBUG">DEBUG</option>
                  <option value="WARNING">WARNING</option>
                </select>

                {/* Clear Logs Button */}
                <button
                  onClick={clearLogs}
                  className="bg-coffee-medium hover:bg-coffee-dark text-coffee-cream px-3 py-1 rounded text-sm"
                >
                  Очистить
                </button>

                {/* Close Button */}
                <button
                  onClick={() => setShowLogsModal(false)}
                  className="text-coffee-cream hover:text-white"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>

            {/* Modal Body - Logs Container */}
            <div className="flex-1 overflow-hidden">
              <div 
                ref={logsContainerRef}
                className="h-full overflow-y-auto p-4 space-y-2 bg-gray-900 text-green-400 font-mono text-sm"
              >
                {filteredLogs.length === 0 ? (
                  <div className="text-gray-500 text-center py-8">
                    {logs.length === 0 ? 'Логи не найдены' : 'Нет логов для выбранного фильтра'}
                  </div>
                ) : (
                  filteredLogs.map((log, index) => (
                    <div key={index} className="flex space-x-3 hover:bg-gray-800 px-2 py-1 rounded">
                      {/* Timestamp */}
                      <span className="text-blue-400 shrink-0 w-24">
                        {log.timestamp.slice(11, 19)}
                      </span>
                      
                      {/* Level */}
                      <span className={`shrink-0 w-16 font-semibold ${
                        log.level === 'ERROR' ? 'text-red-400' :
                        log.level === 'WARNING' ? 'text-yellow-400' :
                        log.level === 'DEBUG' ? 'text-purple-400' :
                        'text-green-400'
                      }`}>
                        {log.level}
                      </span>
                      
                      {/* Method */}
                      <span className="text-cyan-400 shrink-0 w-64 truncate" title={log.method}>
                        {log.method}
                      </span>
                      
                      {/* Message */}
                      <span className="text-white flex-1">
                        {log.message}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-coffee-medium bg-coffee-medium/50">
              <div className="flex items-center justify-between text-sm text-coffee-cream">
                <span>
                  Показано: {filteredLogs.length} из {logs.length} записей
                </span>
                <span>
                  Обновление: {status?.state === 'running' ? 'автоматически' : 'вручную'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StatusDashboard 