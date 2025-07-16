# /src/webapp/frontend/Dockerfile

FROM node:22-alpine

WORKDIR /app

# Копируем package.json и package-lock.json (если есть)
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем остальные файлы
COPY . .

# Экспозируем порт
EXPOSE 3005

# Запускаем dev server для разработки (в продакшене будет nginx)
CMD ["npm", "run", "dev"] 