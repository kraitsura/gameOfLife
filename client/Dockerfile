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

# Build the application with the correct base URL for the /simulation path
ENV VITE_BASE_URL=/simulation
RUN bun run build

# Use a lightweight nginx image for serving static files
FROM nginx:alpine

# Copy only the built files
COPY --from=builder /app/dist /usr/share/nginx/html/simulation

# Use a minimal nginx configuration
RUN echo 'server { \
    listen 80; \
    location /simulation { \
        alias /usr/share/nginx/html/simulation; \
        try_files $uri $uri/ /simulation/index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
