# Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Route all to index.html for SPA; tweak if you have a different path
RUN printf 'try_files $uri /index.html;\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80


