# Dev-only image: a Node container running the Vite dev server.

FROM node:20-alpine

WORKDIR /app

# Install dependencies as their OWN layer: Docker caches it, so source
# edits don't trigger a full reinstall — only a package.json change does.
COPY package*.json ./
RUN npm install

# Source is NOT copied here: in dev, docker-compose.override.yml mounts
# ./frontend over /app, so the container always runs  live files
# (same pattern as the backend's uvicorn --reload).
CMD ["npm", "run", "dev"]
