# Stage 0: Base Dependencies
FROM node:24 AS deps

WORKDIR /app

COPY package*.json /app/

RUN npm install --legacy-peer-deps

# Stage 1: Development
FROM deps AS dev
COPY ./ /app/
# The following is just default, but can be overridden
CMD ["npm", "run", "dev", "--", "--host"]

# Stage 2: Build Stage
FROM deps AS build-stage
ARG CACHEBUST=1
COPY ./ /app/
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Stage 3: Production Nginx
FROM nginx:1

COPY --from=build-stage /app/dist/ /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf
