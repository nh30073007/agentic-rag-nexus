#!/bin/bash
# Cloud-init script for EC2 launch
# Paste this in "Advanced details > User data" when launching EC2

apt-get update -y
apt-get install -y docker.io docker-compose git

systemctl start docker
systemctl enable docker

# Clone repo (replace with your GitHub repo)
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/agentic-rag-nexus.git
cd agentic-rag-nexus

# Create .env from example
cp .env.example .env
# Note: Manually edit .env with real API keys

# Start services
docker-compose -f deployment/docker/docker-compose.yml up -d

echo "✅ Agentic RAG Nexus deployed!"