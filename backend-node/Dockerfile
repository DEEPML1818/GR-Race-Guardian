FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json* /app/backend-node/
WORKDIR /app/backend-node
COPY backend-node/package.json /app/backend-node/package.json
RUN npm install --production
COPY . /app
EXPOSE 3001
CMD ["node", "server.js"]
