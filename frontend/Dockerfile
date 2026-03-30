# Stage 1: Build the frontend with Node.js
FROM node:20-alpine AS build-stage

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend code and build
COPY . .
RUN npm run build

# Stage 2: Serve the build files with Nginx
FROM nginx:stable-alpine AS production-stage

# Copy the build output from the build stage to Nginx's default public directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy a custom Nginx configuration to handle the API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the standard Nginx port
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
