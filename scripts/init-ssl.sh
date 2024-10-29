#!/bin/bash

# Install certbot
apt install -y certbot python3-certbot-nginx

# Stop nginx if running
docker compose down

# Get SSL certificate
certbot certonly --standalone \
  -d aaryareddy.com \
  --email aaryaptm09@gmail.com \
  --agree-tos \
  --no-eff-email \
  --force-renewal

# Copy certificates
cp /etc/letsencrypt/live/aaryareddy.com/fullchain.pem /opt/simulation/nginx/ssl/
cp /etc/letsencrypt/live/aaryareddy.com/privkey.pem /opt/simulation/nginx/ssl/

# Set permissions
chmod 644 /opt/simulation/nginx/ssl/fullchain.pem
chmod 644 /opt/simulation/nginx/ssl/privkey.pem