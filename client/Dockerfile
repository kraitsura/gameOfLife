# Stage 1: Build the application
FROM oven/bun:1.0.35 as builder
WORKDIR /app
COPY package.json ./
COPY bun.lockb* ./
RUN bun install
COPY . .
RUN bun run build

# Stage 2: Serve the built application
FROM httpd:alpine

# Remove default Apache files
RUN rm -rf /usr/local/apache2/htdocs/*

# Copy the built files directly to the root
COPY --from=builder /app/dist/ /usr/local/apache2/htdocs/

# Apache port
EXPOSE 80