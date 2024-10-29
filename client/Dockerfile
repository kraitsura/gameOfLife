# Use the official Bun image as base
FROM oven/bun:1.0.35 as builder

# Set working directory
WORKDIR /app

# Copy package files first
COPY client/package.json ./

# Copy lockfile if it exists, but don't fail if it doesn't
COPY client/bun.lockb* ./

# Install dependencies without frozen lockfile to allow updates
RUN bun install

# Copy source files
COPY client/ .

# Build the application with the correct base URL for the /simulation path
ENV VITE_BASE_URL=/simulation
RUN bun run build

# Use a lightweight nginx image for serving static files
FROM nginx:alpine

# Copy only the built files
COPY --from=builder /app/dist /usr/share/nginx/html/simulation

# Create a more robust nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name _; \
    client_max_body_size 20M; \
    \
    # Compression config \
    gzip on; \
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript; \
    \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN"; \
    add_header X-XSS-Protection "1; mode=block"; \
    \
    location /simulation { \
        alias /usr/share/nginx/html/simulation; \
        try_files $uri $uri/ /simulation/index.html; \
        \
        # Cache static assets \
        location ~* \.(?:css|js|jpg|jpeg|gif|png|ico|cur|gz|svg|svgz|mp4|ogg|ogv|webm|htc)$ { \
            expires 1M; \
            access_log off; \
            add_header Cache-Control "public"; \
        } \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]