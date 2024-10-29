# Build stage
FROM oven/bun:1.0.35 as builder

WORKDIR /app

COPY package.json ./
COPY bun.lockb* ./

RUN bun install

COPY . .

RUN bun run build

# Final stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html/simulation

COPY nginx.conf /etc/nginx/conf.d/default.conf