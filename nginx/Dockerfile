# Use the official nginx image
FROM nginx:alpine

# Install required packages
RUN apk add --no-cache openssl curl

# Create directory for SSL certificates
RUN mkdir -p /etc/nginx/ssl

# Create directory for certbot challenges
RUN mkdir -p /var/www/certbot

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx/conf.d/app.conf /etc/nginx/conf.d/

# Generate self-signed SSL certificate for initial setup
RUN openssl req -x509 -nodes -days 365 \
    -subj "/C=US/ST=CA/O=MyOrg/CN=aaryareddy.com" \
    -addext "subjectAltName=DNS:aaryareddy.com" \
    -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/privkey.pem \
    -out /etc/nginx/ssl/fullchain.pem

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose ports
EXPOSE 80
EXPOSE 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
