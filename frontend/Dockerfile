FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Same-origin relative path: nginx proxies /api/ to the backend service,
# so the browser never needs cross-origin requests (no CORS in production).
ENV VITE_API_BASE_URL=/api/v1
# Fixed port the phone-camera pairing link always points to (see CamerasPage),
# regardless of which port/scheme the admin is currently browsing from.
ENV VITE_PHONE_PAIRING_HTTPS_PORT=8443
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache openssl
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# NOT under conf.d/: that directory's *.conf files are all auto-included at
# the top level by the base image's nginx.conf, where a bare `location`
# block (as opposed to one nested in a `server`) is a syntax error.
RUN mkdir -p /etc/nginx/snippets
COPY common-locations.conf /etc/nginx/snippets/common-locations.conf
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
EXPOSE 80 443
ENTRYPOINT ["docker-entrypoint.sh"]
