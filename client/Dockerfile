# Build stage
FROM oven/bun:1.0.35 as builder

WORKDIR /app

COPY client/package.json ./
COPY client/bun.lockb* ./

RUN bun install

COPY client/ .

ENV VITE_BASE_URL=/simulation
ENV VITE_API_URL=/simulation/api
ENV VITE_WS_URL=/simulation/ws

RUN bun run build

# Final stage
FROM alpine:3.18

# Create directory that matches the volume mount point
WORKDIR /app/dist

# Copy built files from builder stage to the volume mount point
COPY --from=builder /app/dist .

# Keep container running to maintain volume
CMD ["tail", "-f", "/dev/null"]