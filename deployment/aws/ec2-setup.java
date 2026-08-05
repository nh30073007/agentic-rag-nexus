#!/bin/bash
# ============================================
# AWS EC2 Setup Script for Agentic RAG Nexus
# Run on: Ubuntu 22.04 LTS
# ============================================

set -e

echo "🚀 Starting EC2 setup for Agentic RAG Nexus..."

# Update system
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Install Python & pip
sudo apt-get install -y python3-pip

# Create app directory
mkdir -p ~/agentic-rag-nexus
cd ~/agentic-rag-nexus

# Note: User needs to upload project files here
# Or clone from GitHub

echo "✅ EC2 setup complete!"
echo "Next steps:"
echo "1. Upload your project files to ~/agentic-rag-nexus"
echo "2. Create .env file with your API keys"
echo "3. Run: docker-compose -f deployment/docker/docker-compose.yml up -d"