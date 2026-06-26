# Production image for the SHIELD web app (Next.js standalone output).
#
# Build from the REPO ROOT (the pnpm workspace + packages/* are needed):
#   docker build -f apps/web/Dockerfile -t shield-web .
#
# Note: validate this build in a Linux Docker environment — Next's standalone
# copy step uses symlinks that fail on Windows (EPERM) but work in Docker.

FROM node:20-bookworm-slim AS deps
RUN corepack enable
WORKDIR /repo
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages packages
RUN pnpm install --frozen-lockfile

FROM node:20-bookworm-slim AS build
RUN corepack enable
WORKDIR /repo
COPY --from=deps /repo/node_modules node_modules
COPY . .
RUN pnpm -F web build

FROM node:20-bookworm-slim AS run
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
# Standalone bundle + static assets + public dir.
COPY --from=build /repo/apps/web/.next/standalone ./
COPY --from=build /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=build /repo/apps/web/public ./apps/web/public
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
