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

# Copy the built files from builder stage to Apache's default public directory
COPY --from=builder /app/dist/ /usr/local/apache2/htdocs/simulation/

# Apache port
EXPOSE 80

# Apache runs by default, no need for explicit CMD