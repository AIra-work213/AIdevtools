#!/bin/bash

echo "🚀 Deploying to server..."

ssh myuser@89.169.132.244 << 'EOF'
cd ~/ai_devtools
echo "📥 Pulling latest code..."
git pull

echo "🛑 Stopping containers..."
docker-compose down

echo "🏗️  Building new images (this may take a while for headless Chrome)..."
docker-compose build --no-cache backend

echo "🚀 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Checking services..."
docker-compose ps
docker logs testops-backend --tail 20

echo "🎉 Deployment complete!"
EOF
