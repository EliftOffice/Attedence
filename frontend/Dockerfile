# ---- build the Angular app ----
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# defaultConfiguration is "production" (file-replaces environment.ts -> environment.prod.ts)
RUN npx ng build --configuration production

# ---- serve the static bundle with nginx ----
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Angular 17 application builder emits to dist/<project>/browser
COPY --from=build /app/dist/attendance/browser /usr/share/nginx/html
EXPOSE 80
