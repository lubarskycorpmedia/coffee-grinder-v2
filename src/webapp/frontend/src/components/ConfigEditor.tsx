import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm, useFieldArray, Controller } from 'react-hook-form'
import toast from 'react-hot-toast'
import { PlusIcon, TrashIcon, DocumentIcon, CalendarDaysIcon } from '@heroicons/react/24/outline'

interface ProviderConfig {
  query?: string
  category?: string
  published_at?: string
  from_date?: string
  to_date?: string
  language?: string
  limit?: number
  country?: string
  timeframe?: string
}

interface ConfigData {
  [providerName: string]: ProviderConfig
}

interface FormData {
  providers: Array<{
    name: string
    config: ProviderConfig
  }>
}

// Новые интерфейсы для параметров провайдеров
interface ProviderParameters {
  categories: string[]
  languages: string[]
}

interface ParametersData {
  [providerName: string]: ProviderParameters
}

// Компонент для красивого date input
const DateInput = ({ name, register, placeholder }: { 
  name: string, 
  register: any, 
  placeholder?: string 
}) => {
  return (
    <div className="relative group">
      <input
        type="date"
        {...register(name)}
        className="input-field pr-10 cursor-pointer hover:border-coffee-cream/50 focus:border-coffee-cream transition-colors"
        placeholder={placeholder}
        style={{
          colorScheme: 'dark',
        }}
      />
      <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none text-coffee-cream/70 group-hover:text-coffee-cream transition-colors">
        <CalendarDaysIcon className="h-5 w-5" />
      </div>
    </div>
  )
}

// Компонент мультиселекта с чекбоксами
const MultiSelectCheckbox = ({ 
  options, 
  value, 
  onChange, 
  placeholder,
  anyLabel = "Любая"
}: { 
  options: string[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  anyLabel?: string
}) => {
  const [isOpen, setIsOpen] = useState(false)
  
  // Закрываем dropdown при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      if (!target.closest('.multiselect-container')) {
        setIsOpen(false)
      }
    }
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])
  
  // Парсим текущие значения из строки
  const selectedValues = value ? value.split(',').filter(Boolean) : []
  
  const handleOptionChange = (option: string, checked: boolean) => {
    let newValues: string[]
    
    if (option === '') {
      // Выбран "Любая" - сбрасываем все остальные
      newValues = checked ? [] : []
    } else {
      if (checked) {
        // Добавляем опцию, убираем "Любая" если она была
        newValues = [...selectedValues.filter(v => v !== ''), option]
      } else {
        // Убираем опцию
        newValues = selectedValues.filter(v => v !== option)
      }
    }
    
    onChange(newValues.join(','))
  }

  const displayText = () => {
    if (selectedValues.length === 0) {
      return anyLabel
    }
    if (selectedValues.length === 1) {
      return selectedValues[0]
    }
    return `${selectedValues.length} выбрано`
  }

  return (
    <div className="relative multiselect-container">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="input-field text-left flex justify-between items-center w-full"
      >
        <span>{displayText()}</span>
        <svg 
          className={`w-4 h-4 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-coffee-dark border border-coffee-cream/30 rounded-md shadow-lg max-h-60 overflow-auto">
          {/* Опция "Любая" */}
          <label className="flex items-center px-3 py-2 hover:bg-coffee-cream/10 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedValues.length === 0}
              onChange={(e) => handleOptionChange('', e.target.checked)}
              className="mr-2 rounded border-coffee-cream/30 text-coffee-cream focus:ring-coffee-cream"
            />
            <span className="text-coffee-cream">{anyLabel}</span>
          </label>
          
          {/* Остальные опции */}
          {options.map((option) => (
            <label key={option} className="flex items-center px-3 py-2 hover:bg-coffee-cream/10 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedValues.includes(option)}
                onChange={(e) => handleOptionChange(option, e.target.checked)}
                className="mr-2 rounded border-coffee-cream/30 text-coffee-cream focus:ring-coffee-cream"
              />
              <span className="text-coffee-cream">{option}</span>
            </label>
          ))}
          
          {options.length === 0 && (
            <div className="px-3 py-2 text-coffee-cream/60 text-sm">
              {placeholder || "Нет доступных опций"}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const ConfigEditor = () => {
  const queryClient = useQueryClient()
  const [showRawJSON, setShowRawJSON] = useState(false)
  const [rawJSON, setRawJSON] = useState('')

  // Получение текущей конфигурации
  const { data: configData, isLoading } = useQuery<ConfigData>(
    'news-config',
    async () => {
      const response = await fetch('/news/api/config', {
        headers: {
          'X-API-Key': 'development_key'
        }
      })
      if (!response.ok) {
        throw new Error('Failed to fetch config')
      }
      return response.json()
    }
  )

  // Получение параметров провайдеров (категории и языки)
  const { data: parametersData, isLoading: isLoadingParameters } = useQuery<ParametersData>(
    'provider-parameters',
    async () => {
      const response = await fetch('/news/api/parameters', {
        headers: {
          'X-API-Key': 'development_key'
        }
      })
      if (!response.ok) {
        throw new Error('Failed to fetch provider parameters')
      }
      return response.json()
    },
    {
      staleTime: 5 * 60 * 1000, // 5 минут кеша
      cacheTime: 10 * 60 * 1000, // 10 минут в памяти
    }
  )

  // Мутация для сохранения конфигурации
  const saveMutation = useMutation(
    async (data: ConfigData) => {
      const response = await fetch('/news/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'development_key'
        },
        body: JSON.stringify({ providers: data })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save config')
      }
      
      return response.json()
    },
    {
      onSuccess: () => {
        toast.success('Конфигурация сохранена!')
        queryClient.invalidateQueries('news-config')
        queryClient.invalidateQueries('processing-status')
      },
      onError: (error: Error) => {
        toast.error(`Ошибка сохранения: ${error.message}`)
      }
    }
  )

  // React Hook Form
  const { control, handleSubmit, reset, watch } = useForm<FormData>({
    defaultValues: {
      providers: [{ name: '', config: {} }]
    }
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'providers'
  })

  // Обновляем форму при загрузке данных
  useEffect(() => {
    if (configData) {
      const formattedData = Object.entries(configData).map(([name, config]) => ({
        name,
        config
      }))
      
      if (formattedData.length === 0) {
        formattedData.push({ name: '', config: {} })
      }
      
      reset({ providers: formattedData })
      setRawJSON(JSON.stringify(configData, null, 2))
    }
  }, [configData, reset])

  // Следим за изменениями формы для обновления JSON
  const watchedProviders = watch('providers')
  useEffect(() => {
    const configObject: ConfigData = {}
    watchedProviders.forEach(provider => {
      if (provider.name) {
        configObject[provider.name] = provider.config
      }
    })
    setRawJSON(JSON.stringify(configObject, null, 2))
  }, [watchedProviders])

  const onSubmit = (data: FormData) => {
    const configObject: ConfigData = {}
    data.providers.forEach(provider => {
      if (provider.name) {
        // Очищаем пустые значения
        const cleanConfig = Object.fromEntries(
          Object.entries(provider.config).filter(([_, value]) => 
            value !== undefined && value !== null && value !== ''
          )
        )
        configObject[provider.name] = cleanConfig
      }
    })
    
    saveMutation.mutate(configObject)
  }

  const onSaveRawJSON = () => {
    try {
      const parsedConfig = JSON.parse(rawJSON)
      saveMutation.mutate(parsedConfig)
    } catch (error) {
      toast.error('Некорректный JSON')
    }
  }

  const addProvider = () => {
    append({ name: '', config: {} })
  }

  const availableProviders = [
    'thenewsapi', 'newsapi', 'newsdata', 'mediastack', 'gnews'
  ]

  const getProviderPlaceholder = (providerName: string, field: string) => {
    const examples: Record<string, Record<string, string>> = {
      thenewsapi: {
        query: 'artificial intelligence',
        category: 'tech',
        published_at: 'last_24_hours',
        limit: '50'
      },
      newsapi: {
        query: 'AI technology',
        category: 'technology',
        from_date: '2024-01-01',
        language: 'en',
        limit: '100'
      },
      newsdata: {
        query: 'machine learning',
        category: 'technology',
        timeframe: '24',
        language: 'en'
      }
    }
    
    return examples[providerName]?.[field] || ''
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-coffee-dark"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-coffee-cream">
            Конфигурация провайдеров новостей
          </h2>
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={() => setShowRawJSON(!showRawJSON)}
              className="btn-secondary flex items-center space-x-2"
            >
              <DocumentIcon className="h-4 w-4" />
              <span>{showRawJSON ? 'Форма' : 'JSON'}</span>
            </button>
          </div>
        </div>

        <p className="text-coffee-cream text-sm">
          Настройте параметры для каждого провайдера новостей. 
          Каждый провайдер будет обрабатываться отдельно согласно указанным параметрам.
        </p>
      </div>

      {/* JSON Editor */}
      {showRawJSON ? (
        <div className="card">
          <h3 className="text-lg font-medium text-coffee-cream mb-4">
            Редактор JSON
          </h3>
          <div className="space-y-4">
            <textarea
              value={rawJSON}
              onChange={(e) => setRawJSON(e.target.value)}
              className="input-field font-mono text-sm h-64 resize-none"
              placeholder="Введите JSON конфигурацию..."
            />
            <button
              onClick={onSaveRawJSON}
              disabled={saveMutation.isLoading}
              className="btn-primary"
            >
              {saveMutation.isLoading ? 'Сохранение...' : 'Сохранить JSON'}
            </button>
          </div>
        </div>
      ) : (
        /* Form Editor */
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {fields.map((field, index) => (
            <div key={field.id} className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-coffee-cream">
                  Запрос #{index + 1}
                </h3>
                {fields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-red-400 hover:text-red-300 p-1"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Provider Name */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Провайдер *
                  </label>
                  <select
                    {...control.register(`providers.${index}.name`)}
                    className="input-field"
                  >
                    <option value="">Выберите провайдера</option>
                    {availableProviders.map(provider => (
                      <option key={provider} value={provider}>
                        {provider}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Query */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Ключевые слова
                  </label>
                  <input
                    type="text"
                    {...control.register(`providers.${index}.config.query`)}
                    className="input-field"
                    placeholder={getProviderPlaceholder(watchedProviders[index]?.name, 'query')}
                  />
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Категория
                  </label>
                  {watchedProviders[index]?.name && parametersData ? (
                    <Controller
                      name={`providers.${index}.config.category`}
                      control={control}
                      render={({ field }) => (
                        <MultiSelectCheckbox
                          options={parametersData?.[watchedProviders[index].name]?.categories || []}
                          value={field.value || ''}
                          onChange={field.onChange}
                          placeholder="Нет доступных категорий"
                          anyLabel="Любая категория"
                        />
                      )}
                    />
                  ) : (
                    <div className="input-field text-coffee-cream/60">
                      {!watchedProviders[index]?.name 
                        ? "Сначала выберите провайдера" 
                        : isLoadingParameters 
                          ? "Загрузка..." 
                          : "Ошибка загрузки категорий"
                      }
                    </div>
                  )}
                </div>

                {/* Language */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Язык
                  </label>
                  {watchedProviders[index]?.name && parametersData ? (
                    <Controller
                      name={`providers.${index}.config.language`}
                      control={control}
                      render={({ field }) => (
                        <MultiSelectCheckbox
                          options={parametersData?.[watchedProviders[index].name]?.languages || []}
                          value={field.value || ''}
                          onChange={field.onChange}
                          placeholder="Нет доступных языков"
                          anyLabel="Любой язык"
                        />
                      )}
                    />
                  ) : (
                    <div className="input-field text-coffee-cream/60">
                      {!watchedProviders[index]?.name 
                        ? "Сначала выберите провайдера" 
                        : isLoadingParameters 
                          ? "Загрузка..." 
                          : "Ошибка загрузки языков"
                      }
                    </div>
                  )}
                </div>

                {/* Limit */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Лимит статей
                  </label>
                  <input
                    type="number"
                    {...control.register(`providers.${index}.config.limit`, { 
                      valueAsNumber: true,
                      min: 1,
                      max: 1000 
                    })}
                    className="input-field"
                    placeholder="50"
                  />
                </div>

                {/* Published At / Timeframe */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Период публикации
                  </label>
                  <input
                    type="text"
                    {...control.register(`providers.${index}.config.published_at`)}
                    className="input-field"
                    placeholder="last_24_hours, last_7_days"
                  />
                </div>

                {/* From Date */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Дата от
                  </label>
                  <DateInput
                    name={`providers.${index}.config.from_date`}
                    register={control.register}
                    placeholder="Выберите дату начала"
                  />
                </div>

                {/* To Date */}
                <div>
                  <label className="block text-sm font-medium text-coffee-cream mb-1">
                    Дата до
                  </label>
                  <DateInput
                    name={`providers.${index}.config.to_date`}
                    register={control.register}
                    placeholder="Выберите дату окончания"
                  />
                </div>
              </div>
            </div>
          ))}

          {/* Add Provider Button */}
          <div className="text-center">
            <button
              type="button"
              onClick={addProvider}
              className="btn-secondary flex items-center space-x-2 mx-auto"
            >
              <PlusIcon className="h-4 w-4" />
              <span>Добавить запрос</span>
            </button>
          </div>

          {/* Save Button */}
          <div className="card">
            <button
              type="submit"
              disabled={saveMutation.isLoading}
              className="btn-primary w-full"
            >
              {saveMutation.isLoading ? 'Сохранение...' : 'Сохранить конфигурацию'}
            </button>
          </div>
        </form>
      )}

      {/* Help */}
      <div className="card bg-coffee-cream/30">
        <h3 className="text-lg font-medium text-coffee-cream mb-2">
          Справка по параметрам
        </h3>
        <div className="text-sm text-coffee-cream space-y-2">
          <p><strong>query:</strong> Ключевые слова для поиска новостей</p>
          <p><strong>category:</strong> Категория новостей (tech, business, sports, etc.)</p>
          <p><strong>published_at:</strong> Период публикации (last_24_hours, last_7_days)</p>
          <p><strong>from_date/to_date:</strong> Конкретные даты в формате YYYY-MM-DD</p>
          <p><strong>language:</strong> Код языка (en, ru, es, fr, de)</p>
          <p><strong>limit:</strong> Максимальное количество статей для загрузки</p>
        </div>
      </div>
    </div>
  )
}

export default ConfigEditor 