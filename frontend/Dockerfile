FROM node:16-alpine

WORKDIR /app

# Only copy package.json first (since we don't have package-lock.json)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

EXPOSE 3000
CMD ["npm", "start"]
