FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:1.27-alpine AS serve

# Railway assigns a dynamic $PORT the container must bind to; nginx can't read
# env vars directly, so this is templated via the base image's built-in
# envsubst-on-templates entrypoint step (/etc/nginx/templates/*.template ->
# /etc/nginx/conf.d/, run automatically before nginx starts). PORT=80 is the
# fallback for local docker-compose, where it isn't set.
ENV PORT=80

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
