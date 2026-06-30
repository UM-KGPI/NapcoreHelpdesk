FROM node:20-alpine AS builder

WORKDIR /app/frontend

COPY package*.json ./
RUN npm ci

COPY . /app/frontend

# Build with version
ARG VITE_APP_VERSION=0.6.1
ENV VITE_APP_VERSION=$VITE_APP_VERSION
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/frontend/dist /usr/share/nginx/html
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
