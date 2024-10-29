# Use the official Bun image as base
FROM oven/bun:1.0.35 as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY client/package.json client/bun.lockb ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source files
COPY client/ .

# Build the application
RUN bun run build

# Use nginx for serving static files
FROM nginx:alpine

# Copy nginx configuration from the nginx directory
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
