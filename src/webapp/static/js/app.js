// /src/webapp/static/js/app.js

/**
 * Coffee Grinder v2 - Frontend Application
 * Клиентская логика для взаимодействия с API
 */

class CoffeeGrinderApp {
    constructor() {
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.statusTime = document.getElementById('status-time');
        this.statusContainer = document.querySelector('.status');
        this.runForm = document.getElementById('run-form');
        this.submitButton = document.getElementById('submit-button');
        this.alertContainer = document.getElementById('alert-container');
        
        this.init();
    }

    /**
     * Инициализация приложения
     */
    init() {
        this.bindEvents();
        this.loadHealthStatus();
        
        // Автообновление статуса каждые 30 секунд
        setInterval(() => {
            this.loadHealthStatus();
        }, 30000);
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        if (this.runForm) {
            this.runForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.runNewsProcessing();
            });
        }

        // Обработка клавиш
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.runNewsProcessing();
            }
        });
    }

    /**
     * Загрузка статуса здоровья сервиса
     */
    async loadHealthStatus() {
        try {
            const response = await fetch('health');
            const data = await response.json();
            
            if (response.ok) {
                this.updateStatus('healthy', `Сервис работает (v${data.version || 'unknown'})`, data.timestamp);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Ошибка загрузки статуса:', error);
            this.updateStatus('error', 'Сервис недоступен', new Date().toISOString());
        }
    }

    /**
     * Обновление отображения статуса
     * @param {string} status - healthy или error
     * @param {string} text - текст статуса
     * @param {string} timestamp - время последнего обновления
     */
    updateStatus(status, text, timestamp) {
        if (!this.statusIndicator || !this.statusText || !this.statusTime || !this.statusContainer) {
            return;
        }

        // Обновляем классы
        this.statusContainer.className = `status ${status}`;
        this.statusIndicator.className = `status-indicator ${status}`;
        
        // Обновляем текст
        this.statusText.textContent = text;
        
        // Форматируем время
        try {
            const date = new Date(timestamp);
            this.statusTime.textContent = date.toLocaleString('ru-RU');
        } catch (e) {
            this.statusTime.textContent = 'Неизвестно';
        }
    }

    /**
     * Запуск обработки новостей
     */
    async runNewsProcessing() {
        if (!this.runForm || !this.submitButton) {
            return;
        }

        const formData = new FormData(this.runForm);
        const query = formData.get('query') || 'technology';
        const limit = parseInt(formData.get('limit')) || 50;

        // Показываем индикатор загрузки
        this.setLoadingState(true);
        this.clearAlerts();
        
        try {
            const response = await fetch('web/trigger/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    query: query,
                    limit: limit.toString()
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showAlert('success', `Обработка новостей запущена! Запрос: "${data.query}", лимит: ${data.limit}`);
                this.runForm.reset();
                
                // Показываем прогресс
                this.showProgressInfo(data);
            } else {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Ошибка запуска обработки:', error);
            this.showAlert('error', `Ошибка: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Управление состоянием загрузки
     * @param {boolean} loading - включить/выключить состояние загрузки
     */
    setLoadingState(loading) {
        if (!this.submitButton) return;

        if (loading) {
            this.submitButton.disabled = true;
            this.submitButton.innerHTML = '<span class="loading"></span> Запуск...';
        } else {
            this.submitButton.disabled = false;
            this.submitButton.innerHTML = '▶ Запустить обработку';
        }
    }

    /**
     * Показ уведомления
     * @param {string} type - тип уведомления (success, error, info)
     * @param {string} message - текст сообщения
     */
    showAlert(type, message) {
        if (!this.alertContainer) return;

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;

        // Добавляем кнопку закрытия
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.style.cssText = `
            float: right;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            margin-left: 10px;
            opacity: 0.7;
        `;
        closeButton.onclick = () => alertDiv.remove();
        alertDiv.appendChild(closeButton);

        this.alertContainer.appendChild(alertDiv);

        // Автоудаление через 10 секунд
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 10000);
    }

    /**
     * Очистка всех уведомлений
     */
    clearAlerts() {
        if (this.alertContainer) {
            this.alertContainer.innerHTML = '';
        }
    }

    /**
     * Показ информации о прогрессе
     * @param {object} data - данные ответа от API
     */
    showProgressInfo(data) {
        const progressMessage = `
            <strong>Задача поставлена в очередь:</strong><br>
            📊 Запрос: ${data.query}<br>
            📏 Лимит статей: ${data.limit}<br>
            ⏰ Время запуска: ${new Date(data.timestamp).toLocaleString('ru-RU')}<br>
            💡 Обработка выполняется в фоновом режиме
        `;
        
        this.showAlert('info', progressMessage);
    }

    /**
     * Копирование API URL в буфер обмена
     * @param {string} url - URL для копирования
     */
    async copyToClipboard(url) {
        try {
            await navigator.clipboard.writeText(url);
            this.showAlert('success', `Скопировано: ${url}`);
        } catch (err) {
            console.error('Ошибка копирования:', err);
            
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = url;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showAlert('success', `Скопировано: ${url}`);
            } catch (e) {
                this.showAlert('error', 'Не удалось скопировать URL');
            }
            
            document.body.removeChild(textArea);
        }
    }

    /**
     * Форматирование числа с разделителями
     * @param {number} num - число для форматирования
     * @returns {string} отформатированное число
     */
    formatNumber(num) {
        return new Intl.NumberFormat('ru-RU').format(num);
    }

    /**
     * Валидация формы
     * @returns {boolean} результат валидации
     */
    validateForm() {
        const limitInput = document.getElementById('limit');
        if (!limitInput) return true;

        const limit = parseInt(limitInput.value);
        if (isNaN(limit) || limit < 1 || limit > 1000) {
            this.showAlert('error', 'Лимит должен быть числом от 1 до 1000');
            limitInput.focus();
            return false;
        }

        return true;
    }
}

/**
 * Утилиты
 */
const Utils = {
    /**
     * Дебаунсинг функции
     * @param {function} func - функция для дебаунсинга
     * @param {number} wait - задержка в миллисекундах
     * @returns {function} дебаунснутая функция
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Проверка доступности API
     * @returns {Promise<boolean>} результат проверки
     */
    async checkApiAvailability() {
        try {
            const response = await fetch('health', { 
                method: 'HEAD',
                cache: 'no-cache'
            });
            return response.ok;
        } catch {
            return false;
        }
    }
};

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('☕ Coffee Grinder v2 - Frontend загружен');
    
    // Создаем экземпляр приложения
    window.coffeeGrinderApp = new CoffeeGrinderApp();
    
    // Добавляем обработчики для API ссылок
    document.querySelectorAll('.api-link').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const url = window.location.origin + link.getAttribute('href');
            await window.coffeeGrinderApp.copyToClipboard(url);
        });
    });

    // Показываем сообщение о готовности
    console.log('✅ Интерфейс готов к работе');
});

// Обработка ошибок JavaScript
window.addEventListener('error', (event) => {
    console.error('JavaScript ошибка:', event.error);
    
    if (window.coffeeGrinderApp) {
        window.coffeeGrinderApp.showAlert('error', 
            'Произошла ошибка JavaScript. Проверьте консоль браузера.');
    }
});

// Экспорт для возможного использования в тестах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CoffeeGrinderApp, Utils };
} 