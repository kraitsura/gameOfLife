# Stage 1: Build the application
FROM oven/bun:1.0.35 as builder
WORKDIR /app
COPY package.json ./
COPY bun.lockb* ./
RUN bun install
COPY . .
RUN bun run build

# Stage 2: Serve the built application
FROM nginx:alpine

# Install wget for health check (instead of curl)
RUN apk add --no-cache wget

COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy the built files to nginx's default serving directory
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Create a simple health check file
RUN echo "OK" > /usr/share/nginx/html/health.txt

# Apache port
EXPOSE 80