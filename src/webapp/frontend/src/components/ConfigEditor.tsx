import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm, useFieldArray, Controller } from 'react-hook-form'
import toast from 'react-hot-toast'
import { PlusIcon, TrashIcon, DocumentIcon, CalendarDaysIcon } from '@heroicons/react/24/outline'

interface ProviderConfig {
  [key: string]: any // Динамическая структура на основе JSON параметров
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

// Интерфейс для данных форм провайдеров
interface ProviderFormData {
  url: string
  fields: Record<string, string>
}

interface ProviderParametersData {
  [providerName: string]: ProviderFormData
}

// Компонент для красивого datetime input
const DateTimeInput = ({ name, register, placeholder }: { 
  name: string, 
  register: any, 
  placeholder?: string 
}) => {
  return (
    <div className="relative group">
      <input
        type="datetime-local"
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

// Функция для получения полей формы из данных бекенда
const getProviderFormFields = (providerName: string, providerParametersData: ProviderParametersData | undefined): Record<string, string> => {
  if (!providerParametersData) return {}
  return providerParametersData[providerName]?.fields || {}
}

// Функция для получения URL эндпоинта провайдера
const getProviderEndpointUrl = (providerName: string, providerParametersData: ProviderParametersData | undefined): string => {
  if (!providerParametersData) return ''
  return providerParametersData[providerName]?.url || ''
}

// Компонент для отображения одного поля формы
const DynamicFormField = ({ 
  fieldKey, 
  fieldLabel, 
  providerIndex,
  control,
  parametersData, 
  providerName 
}: {
  fieldKey: string
  fieldLabel: string
  providerIndex: number
  control: any
  parametersData: ParametersData | undefined
  providerName: string
}) => {
  // Определяем тип поля на основе названия
  const getFieldType = (key: string) => {
    const lowerKey = key.toLowerCase()
    if (lowerKey.includes('date') || lowerKey.includes('published')) {
      return 'date'
    }
    if (lowerKey.includes('limit') || lowerKey.includes('count') || lowerKey.includes('size')) {
      return 'number'
    }
    if (lowerKey.includes('category') || lowerKey.includes('categories')) {
      return 'multiselect-categories'
    }
    if (lowerKey.includes('language') || lowerKey.includes('lang')) {
      return 'multiselect-languages'
    }
    return 'text'
  }

  const fieldType = getFieldType(fieldKey)

  switch (fieldType) {
    case 'date':
      return (
        <div>
          <label className="block text-sm font-medium text-coffee-cream mb-1">
            {fieldLabel}
          </label>
          <DateTimeInput
            name={`providers.${providerIndex}.config.${fieldKey}`}
            register={control.register}
            placeholder={`Выберите ${fieldLabel.toLowerCase()}`}
          />
        </div>
      )

    case 'number':
      return (
        <div>
          <label className="block text-sm font-medium text-coffee-cream mb-1">
            {fieldLabel}
          </label>
          <input
            type="number"
            {...control.register(`providers.${providerIndex}.config.${fieldKey}`, { 
              valueAsNumber: true 
            })}
            className="input-field"
            placeholder={fieldLabel}
            min={1}
            max={1000}
          />
        </div>
      )

    case 'multiselect-categories':
      return (
        <div>
          <label className="block text-sm font-medium text-coffee-cream mb-1">
            {fieldLabel}
          </label>
          {providerName && parametersData?.[providerName] ? (
            <Controller
              name={`providers.${providerIndex}.config.${fieldKey}`}
              control={control}
              render={({ field }) => (
                <MultiSelectCheckbox
                  options={parametersData[providerName].categories || []}
                  value={field.value || ''}
                  onChange={field.onChange}
                  placeholder="Нет доступных категорий"
                  anyLabel="Любая категория"
                />
              )}
            />
          ) : (
            <div className="input-field text-coffee-cream/60">
              {!providerName 
                ? "Сначала выберите провайдера" 
                : "Загрузка категорий..."
              }
            </div>
          )}
        </div>
      )

    case 'multiselect-languages':
      return (
        <div>
          <label className="block text-sm font-medium text-coffee-cream mb-1">
            {fieldLabel}
          </label>
          {providerName && parametersData?.[providerName] ? (
            <Controller
              name={`providers.${providerIndex}.config.${fieldKey}`}
              control={control}
              render={({ field }) => (
                <MultiSelectCheckbox
                  options={parametersData[providerName].languages || []}
                  value={field.value || ''}
                  onChange={field.onChange}
                  placeholder="Нет доступных языков"
                  anyLabel="Любой язык"
                />
              )}
            />
          ) : (
            <div className="input-field text-coffee-cream/60">
              {!providerName 
                ? "Сначала выберите провайдера" 
                : "Загрузка языков..."
              }
            </div>
          )}
        </div>
      )

    default:
      return (
        <div>
          <label className="block text-sm font-medium text-coffee-cream mb-1">
            {fieldLabel}
          </label>
          <input
            type="text"
            {...control.register(`providers.${providerIndex}.config.${fieldKey}`)}
            className="input-field"
            placeholder={fieldLabel}
          />
        </div>
      )
  }
}

const ConfigEditor = () => {
  const queryClient = useQueryClient()
  const [showRawJSON, setShowRawJSON] = useState(false)
  const [rawJSON, setRawJSON] = useState('')
  const [selectedProviderToAdd, setSelectedProviderToAdd] = useState('')

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
      const response = await fetch('/news/api/available_parameter_values', {
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

  // Получение параметров форм провайдеров
  const { data: providerParametersData, isLoading: isLoadingProviderParameters } = useQuery<ProviderParametersData>(
    'provider-form-parameters',
    async () => {
      const response = await fetch('/news/api/provider_parameters', {
        headers: {
          'X-API-Key': 'development_key'
        }
      })
      if (!response.ok) {
        throw new Error('Failed to fetch provider form parameters')
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
        body: JSON.stringify(data)
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
  const { control, handleSubmit, reset, watch, setValue } = useForm<FormData>({
    defaultValues: {
      providers: []
    }
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'providers'
  })

  // Получаем список доступных провайдеров из providerParametersData
  const availableProviders = providerParametersData ? Object.keys(providerParametersData) : []

  // Обновляем форму при загрузке данных
  useEffect(() => {
    if (configData && providerParametersData) {
      const formattedData: FormData['providers'] = []
      
      // Проходим по всем ключам из JSON конфигурации
      Object.entries(configData).forEach(([providerName, config]) => {
        // ИГНОРИРУЕМ провайдеров которых нет в новой системе
        if (!providerParametersData[providerName]) {
          console.log(`Ignoring unknown provider: ${providerName}`)
          return
        }
        
        // Получаем доступные поля для этого провайдера из get_provider_parameters
        const availableFields = getProviderFormFields(providerName, providerParametersData)
        
        // Создаем новый конфиг только с совпадающими полями
        const filteredConfig: ProviderConfig = {}
        Object.keys(availableFields).forEach(fieldKey => {
          if (config[fieldKey] !== undefined) {
            filteredConfig[fieldKey] = config[fieldKey]
          }
        })
        
        formattedData.push({
          name: providerName,
          config: filteredConfig
        })
      })
      
      reset({ providers: formattedData })
      setRawJSON(JSON.stringify(configData, null, 2))
    }
  }, [configData, providerParametersData, reset])

  // Следим за изменениями формы для обновления JSON
  const watchedProviders = watch('providers')
  useEffect(() => {
    const configObject: ConfigData = {}
    watchedProviders.forEach(provider => {
      if (provider.name) {
        // Фильтруем пустые значения как в onSubmit
        const cleanConfig = Object.fromEntries(
          Object.entries(provider.config).filter(([_, value]) => {
            if (value === undefined || value === null || value === '') return false
            if (typeof value === 'number' && isNaN(value)) return false
            if (typeof value === 'string' && value.trim() === '') return false
            return true
          })
        )
        configObject[provider.name] = cleanConfig
      }
    })
    setRawJSON(JSON.stringify(configObject, null, 2))
  }, [watchedProviders])

  const onSubmit = (data: FormData) => {
    console.log('=== ОТЛАДКА СОХРАНЕНИЯ ===')
    console.log('Полные данные формы:', JSON.stringify(data, null, 2))
    data.providers.forEach((provider, i) => {
      console.log(`Provider ${i}:`, provider.name)
      console.log(`Config ${i}:`, provider.config)
      console.log(`Config keys ${i}:`, Object.keys(provider.config || {}))
    })
    
    const configObject: ConfigData = {}
    data.providers.forEach(provider => {
      if (provider.name) {
        console.log(`🔍 Исходная конфигурация для ${provider.name}:`, provider.config)
        
        // Очищаем пустые значения (исключаем undefined, null, пустые строки и NaN)
        const cleanConfig = Object.fromEntries(
          Object.entries(provider.config).filter(([key, value]) => {
            const shouldKeep = !(
              value === undefined || 
              value === null || 
              value === '' ||
              (typeof value === 'number' && isNaN(value)) ||
              (typeof value === 'string' && value.trim() === '')
            )
            
            if (!shouldKeep) {
              console.log(`🚫 Исключаем поле ${key}:`, value, typeof value)
            }
            
            return shouldKeep
          })
        )
        console.log(`✅ Очищенная конфигурация для ${provider.name}:`, cleanConfig)
        configObject[provider.name] = cleanConfig
      }
    })
    
    console.log('Итоговый объект:', configObject)
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

  // Добавление нового провайдера
  const handleAddProvider = () => {
    if (!selectedProviderToAdd) {
      toast.error('Выберите провайдера для добавления')
      return
    }
    
    append({ 
      name: selectedProviderToAdd, 
      config: {} 
    })
    setSelectedProviderToAdd('')
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
          {fields.map((field, index) => {
            const providerName = watchedProviders[index]?.name
            const formFields = getProviderFormFields(providerName, providerParametersData)
            const endpointUrl = getProviderEndpointUrl(providerName, providerParametersData)

            return (
              <div key={field.id} className="card">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-coffee-cream">
                      Запрос #{index + 1}
                    </h3>
                    {endpointUrl && (
                      <p className="text-sm text-coffee-cream/70 mt-1">
                        Эндпоинт: {endpointUrl}
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-red-400 hover:text-red-300 p-1"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Provider Name */}
                  <div className="md:col-span-2">
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

                  {/* Динамические поля на основе get_provider_parameters */}
                  {providerName && Object.entries(formFields).map(([fieldKey, fieldLabel]) => (
                    <DynamicFormField
                      key={fieldKey}
                      fieldKey={fieldKey}
                      fieldLabel={fieldLabel}
                      providerIndex={index}
                      control={control}
                      parametersData={parametersData}
                      providerName={providerName}
                    />
                  ))}

                  {/* Сообщение если провайдер не выбран */}
                  {!providerName && (
                    <div className="md:col-span-2 p-4 bg-coffee-cream/10 rounded-md">
                      <p className="text-coffee-cream/70 text-center">
                        Выберите провайдера для отображения доступных полей
                      </p>
                    </div>
                  )}

                  {/* Сообщение если нет доступных полей */}
                  {providerName && Object.keys(formFields).length === 0 && (
                    <div className="md:col-span-2 p-4 bg-orange-500/10 rounded-md">
                      <p className="text-orange-400 text-center">
                        {isLoadingProviderParameters 
                          ? "Загрузка полей формы..." 
                          : "Нет доступных полей для этого провайдера"
                        }
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )
          })}

          {/* Add Provider Section */}
          <div className="card">
            <h3 className="text-lg font-medium text-coffee-cream mb-4">
              Добавить провайдера
            </h3>
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <select
                  value={selectedProviderToAdd}
                  onChange={(e) => setSelectedProviderToAdd(e.target.value)}
                  className="input-field"
                  disabled={isLoadingProviderParameters}
                >
                  <option value="">
                    {isLoadingProviderParameters 
                      ? "Загрузка провайдеров..." 
                      : "Выберите провайдера для добавления"
                    }
                  </option>
                  {availableProviders.map(provider => (
                    <option key={provider} value={provider}>
                      {provider}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={handleAddProvider}
                disabled={!selectedProviderToAdd || isLoadingProviderParameters}
                className="btn-secondary flex items-center space-x-2"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Добавить</span>
              </button>
            </div>
            
            {/* Пустое состояние */}
            {fields.length === 0 && (
              <div className="mt-4 p-6 bg-coffee-cream/5 rounded-lg border-2 border-dashed border-coffee-cream/20">
                <div className="text-center">
                  <p className="text-coffee-cream/70 mb-2">
                    Нет настроенных провайдеров
                  </p>
                  <p className="text-sm text-coffee-cream/50">
                    Выберите провайдера выше для создания первой конфигурации
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Save Button */}
          {fields.length > 0 && (
            <div className="card">
              <button
                type="submit"
                disabled={saveMutation.isLoading}
                className="btn-primary w-full"
              >
                {saveMutation.isLoading ? 'Сохранение...' : 'Сохранить конфигурацию'}
              </button>
            </div>
          )}
        </form>
      )}

      {/* Help */}
      <div className="card bg-coffee-cream/30">
        <h3 className="text-lg font-medium text-coffee-cream mb-2">
          О динамических формах
        </h3>
        <div className="text-sm text-coffee-cream space-y-2">
          <p><strong>Автоматическая генерация:</strong> Поля форм создаются автоматически на основе JSON файлов параметров каждого провайдера</p>
          <p><strong>Умная загрузка:</strong> При загрузке конфигурации заполняются только те поля, которые совпадают с доступными параметрами</p>
          <p><strong>Множественные запросы:</strong> Можно добавить несколько конфигураций для одного провайдера</p>
          <p><strong>Полная перезапись:</strong> При сохранении файл конфигурации полностью перезаписывается новыми данными</p>
        </div>
      </div>
    </div>
  )
}

export default ConfigEditor 