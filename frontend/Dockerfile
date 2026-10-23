# Dev-only image: a Node container running the Vite dev server.

FROM node:20-alpine

WORKDIR /app

# Install dependencies as their OWN layer: Docker caches it, so source
# edits don't trigger a full reinstall — only a package.json change does.
# This also pre-populates the frontend_node_modules volume on first run.
COPY package*.json ./
RUN npm install --no-audit --no-fund

# Source is NOT copied here: in dev, docker-compose.override.yml mounts
# ./frontend over /app, so the container always runs  live files
# (same pattern as the backend's uvicorn --reload).

# On every start, re-sync node_modules with the current package.json
# (see entrypoint.sh) before handing over to CMD. This is what makes
# `docker compose restart frontend` pick up newly added dependencies —
# no --build, no volume nuking needed.
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["npm", "run", "dev"]
