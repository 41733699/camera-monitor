FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

# 可通过 npm mirror 加速（默认用官方源）
ARG NPM_REGISTRY=https://registry.npmjs.org
RUN npm install --registry=${NPM_REGISTRY}

COPY . .

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
