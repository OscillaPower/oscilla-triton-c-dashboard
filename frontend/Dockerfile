# https://github.com/vercel/next.js/blob/af9b229074e39617bdd32d390fdc8f6a36d7bcde/examples/with-docker/Dockerfile#L1
# Use Node.js 18 Alpine as base image
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Install compatibility libraries for Alpine
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN npm ci  # Install dependencies using npm

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Install build tools to rebuild native modules
RUN apk add --no-cache python3 make g++   # Install build tools
RUN npm rebuild sqlite3                   # Rebuild sqlite3 for Alpine platform

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

# Add necessary user and group for Next.js
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy public assets from the builder stage
COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Copy build artifacts from the builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Run the application as the nextjs user
USER nextjs

# Expose the necessary port
EXPOSE 3000

# Set environment variables for running the application
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application using the Next.js standalone output
CMD ["node", "server.js"]
