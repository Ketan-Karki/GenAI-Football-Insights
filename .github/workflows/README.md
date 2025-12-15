# GitHub Actions CI/CD Setup

This workflow automatically deploys your application to DigitalOcean whenever you push to the `main` branch.

## Setup Instructions

### 1. Generate SSH Key Pair (if you don't have one)

On your local machine:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions_key
```

### 2. Add Public Key to Droplet

Copy the public key to your droplet:

```bash
ssh-copy-id -i ~/.ssh/github_actions_key.pub ketan@159.65.154.80
```

Or manually:

```bash
# Display public key
cat ~/.ssh/github_actions_key.pub

# SSH to droplet
ssh ketan@159.65.154.80

# Add to authorized_keys
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
```

### 3. Add Secrets to GitHub Repository

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

**DROPLET_IP**

```
159.65.154.80
```

**DROPLET_USER**

```
ketan
```

**SSH_PRIVATE_KEY**

```
# Copy the entire private key including header and footer
cat ~/.ssh/github_actions_key

# It should look like:
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
-----END OPENSSH PRIVATE KEY-----
```

### 4. Configure Sudoers for Passwordless Service Restart

On your droplet:

```bash
sudo visudo
```

Add this line at the end:

```
ketan ALL=(ALL) NOPASSWD: /bin/systemctl restart football-api, /bin/systemctl restart football-ml, /bin/systemctl restart football-frontend, /bin/systemctl status football-api, /bin/systemctl status football-ml, /bin/systemctl status football-frontend
```

Save and exit (Ctrl+X, Y, Enter).

### 5. Test the Workflow

1. Make a small change to your code
2. Commit and push to main branch:
   ```bash
   git add .
   git commit -m "Test CI/CD pipeline"
   git push origin main
   ```
3. Go to GitHub → Actions tab to see the deployment progress

## Workflow Details

The workflow:

1. ✅ Checks out the latest code
2. ✅ SSHs into your droplet
3. ✅ Pulls latest changes from GitHub
4. ✅ Builds frontend (Next.js)
5. ✅ Builds backend (Go)
6. ✅ Updates ML service dependencies
7. ✅ Restarts all services
8. ✅ Checks service status

## Troubleshooting

### SSH Connection Failed

- Verify SSH key is correctly added to GitHub secrets
- Ensure public key is in droplet's `~/.ssh/authorized_keys`
- Check droplet firewall allows SSH (port 22)

### Build Failed

- Check if all dependencies are installed on droplet
- Verify Node.js, Go, and Python versions are correct
- Check disk space: `df -h`

### Service Restart Failed

- Verify sudoers configuration
- Check service logs: `sudo journalctl -u football-api -n 50`

## Manual Deployment

If you need to deploy manually:

```bash
ssh ketan@159.65.154.80
cd /var/www/football-prediction
git pull origin main
# Follow build steps from workflow
```
