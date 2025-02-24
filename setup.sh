#!/bin/bash

# Retrieve admin and user usernames and passwords
echo -n "Enter admin username: "
read ADMIN_USERNAME

echo -n "Enter admin password: "
read -s ADMIN_PASSWORD

echo -n "Enter user username: "
read USER_USERNAME

echo -n "Enter user password: "
read -s USER_PASSWORD


# Run command function that handles password prompts
run_command() {
    COMMAND_SCRIPT=$(mktemp)
    cat > ${COMMAND_SCRIPT} <<EOF
#!/usr/bin/expect -f
set timeout -1
spawn $1
expect {
    "Password:" {
        send "${ADMIN_PASSWORD}\r"
        exp_continue
    }
    eof
}
EOF
    chmod +x ${COMMAND_SCRIPT}
    ${COMMAND_SCRIPT}
    rm ${COMMAND_SCRIPT}
}


# TODO: check distribution

# TODO: check architecture

# TODO: check admin & user accounts are created

# TODO: check current user is user account (repository should be in user account)


# Switch to admin account
echo "Switching to admin account..."
run_command "su - ${ADMIN_USERNAME}"
echo "Switched to admin account."


# Update and upgrade packages
echo "Updating package list..."
run_command "sudo apt update"
echo "Updated package list."

echo "Upgrading installed packages..."
run_command "sudo apt upgrade -y"
echo "Upgraded installed packages."


# Enable and configure Uncomplicated Firewall (UFW)
echo "Enabling Uncomplicated Firewall..."
run_command "sudo ufw enable"
echo "Enabled Uncomplicated Firewall."

echo "Configuring Uncomplicated Firewall..."
run_command "sudo ufw default deny incoming"
run_command "sudo ufw default allow outgoing"
echo "Configured Uncomplicated Firewall."

# Install necessary packages
echo "Installing necessary packages..."
run_command "sudo apt install -y pipx"
run_command "sudo apt install -y xserver-xorg xinit openbox"
run_command "sudo apt install -y libreoffice"
run_command "sudo apt install -y vlc"
echo "Installed necessary packages."
