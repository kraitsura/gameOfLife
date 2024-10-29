# Use the official nginx image
FROM nginx:alpine

# Install required packages
RUN apk add --no-cache openssl curl

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl && \
    chmod 700 /etc/nginx/ssl

# Generate self-signed SSL certificate
RUN openssl req -x509 -nodes -days 365 \
    -subj "/CN=aaryareddy.com" \
    -addext "subjectAltName=DNS:aaryareddy.com" \
    -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/privkey.pem \
    -out /etc/nginx/ssl/fullchain.pem && \
    chmod 600 /etc/nginx/ssl/privkey.pem /etc/nginx/ssl/fullchain.pem

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx/conf.d/app.conf /etc/nginx/conf.d/

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose ports
EXPOSE 80
EXPOSE 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
