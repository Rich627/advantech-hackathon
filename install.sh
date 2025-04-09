#!/bin/bash

# Update package lists
sudo apt update

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv

# Install Java (required for Greengrass)
sudo apt install -y default-jdk

# Create system user and group for Greengrass
sudo useradd --system --create-home ggc_user
sudo groupadd --system ggc_group

# Install additional required dependencies
sudo apt install -y build-essential
sudo apt install -y wget
sudo apt install -y curl
sudo apt install -y git
sudo apt install -y unzip

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip


# Verify installations
java -version
python3.11 --version
aws --version

# Set up cgroups for Lambda container support
if ! grep -q "cgroup_enable=memory cgroup_memory=1 systemd.unified_cgroup_hierarchy=0" /etc/default/grub; then
    sudo sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="cgroup_enable=memory cgroup_memory=1 systemd.unified_cgroup_hierarchy=0"/' /etc/default/grub
    sudo update-grub
fi

# Install NTP for time synchronization
sudo apt install -y ntp
sudo systemctl start ntp
sudo systemctl enable ntp

# Download Greengrass
cd ~
curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip
unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && rm greengrass-nucleus-latest.zip


# Setup AWS Profile
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set aws_region $AWS_REGION

# Install Greengrass
sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
  -jar ./GreengrassInstaller/lib/Greengrass.jar \
  --aws-region region \ 
  --thing-name MyGreengrassCore \
  --thing-group-name MyGreengrassCoreGroup \
  --thing-policy-name GreengrassV2IoTThingPolicy \
  --tes-role-name GreengrassV2TokenExchangeRole \
  --tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
  --component-default-user ggc_user:ggc_group \
  --provision true \
  --setup-system-service true \
  --deploy-dev-tools true

# sudo chmod 755 /greengrass/v2 && sudo chmod 755 /greengrass


# Verify installation
# aws greengrassv2 list-effective-deployments --core-device-thing-name MyGreengrassCore
