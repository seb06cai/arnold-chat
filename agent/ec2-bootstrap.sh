#!/usr/bin/env bash
# Run this script once after SSHing into a fresh Amazon Linux 2023 t3.small instance.
# Usage: bash ec2-bootstrap.sh
set -euo pipefail

echo "=== 1/3: Adding 1 GB swap ==="
if [ ! -f /swapfile ]; then
  sudo dd if=/dev/zero of=/swapfile bs=128M count=8
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
  echo "Swap configured."
else
  echo "Swap already exists, skipping."
fi
free -h

echo ""
echo "=== 2/3: Installing Docker ==="
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
echo "Docker installed. You must log out and back in for the group to take effect."

echo ""
echo "=== 3/3: Done ==="
echo "Next steps:"
echo "  1. Log out: exit"
echo "  2. Log back in: ssh -i your-key.pem ec2-user@<INSTANCE_IP>"
echo "  3. Verify Docker: docker ps"
echo "  4. Copy agent files from local:"
echo "       scp -i your-key.pem -r /path/to/bluejay/agent/ ec2-user@<INSTANCE_IP>:~/agent/"
echo "  5. On EC2, create ~/agent/.env with your API keys"
echo "  6. Build and run:"
echo "       cd ~/agent && docker build -t arnold-coach . && docker run -d --name arnold --env-file .env --restart unless-stopped arnold-coach"
echo "       docker logs -f arnold"
