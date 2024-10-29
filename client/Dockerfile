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

# Copy the built files to nginx's default serving directory
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Apache port
EXPOSE 80