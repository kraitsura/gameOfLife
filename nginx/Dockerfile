FROM nginx:alpine

# Install bash for potential debugging
RUN apk add --no-cache bash

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# Create cache directories
RUN mkdir -p /var/cache/nginx/client_temp && \
    chmod 755 /var/cache/nginx/client_temp

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]