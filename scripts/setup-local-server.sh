#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting OMC Local Server Setup on $(hostname -I | awk '{print $1}')...${NC}"

# 1. Update and Upgrade
echo -e "${GREEN}[1/5] Updating system packages...${NC}"
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Essentials
echo -e "${GREEN}[2/5] Installing essential packages (curl, git, etc.)...${NC}"
sudo apt-get install -y ca-certificates curl gnupg lsb-release git htop

# 3. Install Docker
echo -e "${GREEN}[3/5] Installing Docker...${NC}"
# Add Docker's official GPG key:
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Configure Docker Permissions
echo -e "${GREEN}[4/5] Configuring Docker permissions for current user...${NC}"
sudo usermod -aG docker $USER
echo "Added $USER to docker group. You may need to log out and back in for this to take effect."

# 5. Create Directory Structure
echo -e "${GREEN}[5/5] Creating project directory...${NC}"
mkdir -p ~/ohmycoins
sudo chown $USER:$USER ~/ohmycoins

echo -e "${GREEN}Setup Complete!${NC}"
echo "Next steps:"
echo "1. Log out and log back in (or run 'newgrp docker')."
echo "2. Configure GitHub Actions Runner or copy project files."
