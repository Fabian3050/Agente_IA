# =============================================================================
# DOCKERFILE MULTI-STAGE: FRONTEND VUE 3 + VITE + NGINX
# =============================================================================

# Etapa 1: Compilación de la aplicación
FROM node:20-alpine AS builder

WORKDIR /app

# Argumentos de compilación opcionales para endpoints de microservicios
ARG VITE_MS4_URL=http://localhost:8000
ARG VITE_MS1_URL=http://localhost:8001
ARG VITE_MS2_URL=http://localhost:8002
ARG VITE_MS3_URL=http://localhost:8003

ENV VITE_MS4_URL=$VITE_MS4_URL
ENV VITE_MS1_URL=$VITE_MS1_URL
ENV VITE_MS2_URL=$VITE_MS2_URL
ENV VITE_MS3_URL=$VITE_MS3_URL

# Copiar manifiestos e instalar dependencias
COPY package*.json ./
RUN npm ci || npm install

# Copiar el código fuente y compilar artefactos para producción
COPY . .
RUN npm run build

# Etapa 2: Servidor Nginx Alpine ultraligero
FROM nginx:1.27-alpine AS runner

# Eliminar configuración por defecto de Nginx
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copiar configuración personalizada optimizada para SPA y reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar artefactos estáticos compilados desde la etapa de construcción
COPY --from=builder /app/dist /usr/share/nginx/html

# Exponer el puerto estándar HTTP
EXPOSE 80

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]

