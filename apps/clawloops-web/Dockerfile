FROM node:22.11.0-alpine AS builder

WORKDIR /app
RUN corepack enable

COPY apps/clawloops-web/package.json /app/package.json
COPY apps/clawloops-web/pnpm-lock.yaml /app/pnpm-lock.yaml
COPY apps/clawloops-web/patches /app/patches
RUN pnpm install --frozen-lockfile

COPY apps/clawloops-web /app
RUN pnpm build

FROM node:22.11.0-alpine

WORKDIR /app
ENV NODE_ENV=production
RUN corepack enable

COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/pnpm-lock.yaml /app/pnpm-lock.yaml
COPY --from=builder /app/node_modules /app/node_modules
COPY --from=builder /app/dist /app/dist

EXPOSE 3000
CMD ["pnpm", "start"]
