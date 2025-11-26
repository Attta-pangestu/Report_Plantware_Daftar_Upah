#!/usr/bin/env node

/**
 * Network Setup Script for Payroll System
 * This script helps configure and run the payroll system for LAN access
 */

const { spawn, exec } = require('child_process');
const os = require('os');
const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const interface of interfaces[name]) {
      // Skip internal and non-IPv4 addresses
      if (interface.family === 'IPv4' && !interface.internal) {
        return interface.address;
      }
    }
  }
  return 'localhost';
}

function runCommand(command, cwd, description) {
  return new Promise((resolve, reject) => {
    log(`\n${colors.cyan}🚀 Starting: ${description}${colors.reset}`);
    log(`📁 Directory: ${cwd}`);
    log(`⚡ Command: ${command}\n`);

    const [cmd, ...args] = command.split(' ');
    const child = spawn(cmd, args, {
      cwd,
      stdio: 'inherit',
      shell: true
    });

    child.on('close', (code) => {
      if (code === 0) {
        log(`\n${colors.green}✅ ${description} completed successfully${colors.reset}`);
        resolve(code);
      } else {
        log(`\n${colors.red}❌ ${description} failed with code ${code}${colors.reset}`);
        reject(new Error(`${description} failed with code ${code}`));
      }
    });

    child.on('error', (error) => {
      log(`\n${colors.red}❌ Error starting ${description}: ${error.message}${colors.reset}`);
      reject(error);
    });
  });
}

function createEnvFile(ipAddress) {
  const envContent = `# Network Configuration for Payroll System
# Generated automatically by network-setup.js

# Backend Configuration
VITE_BACKEND_HOST=${ipAddress}
VITE_BACKEND_PORT=8002

# Development Mode
VITE_DEV_MODE=true

# Database Configuration (if needed)
DB_HOST=localhost
DB_PORT=1433
`;

  const envPath = path.join(__dirname, '..', '.env.network');
  fs.writeFileSync(envPath, envContent);

  log(`\n${colors.green}✅ Created .env.network file with IP: ${ipAddress}${colors.reset}`);
  log(`📄 File location: ${envPath}`);
}

async function main() {
  log(`\n${colors.bright}${colors.blue}🌐 Payroll System Network Setup${colors.reset}`);
  log('=' .repeat(50));

  try {
    // Get local IP address
    const localIP = getLocalIP();
    log(`\n${colors.yellow}📡 Detected Local IP: ${localIP}${colors.reset}`);

    // Create environment file
    createEnvFile(localIP);

    const projectRoot = path.join(__dirname, '..');
    const backendDir = path.join(projectRoot, 'backend');
    const frontendDir = path.join(projectRoot, 'frontend');

    log(`\n${colors.cyan}📂 Project Structure:${colors.reset}`);
    log(`   📁 Project Root: ${projectRoot}`);
    log(`   📁 Backend: ${backendDir}`);
    log(`   📁 Frontend: ${frontendDir}`);

    log(`\n${colors.bright}${colors.magenta}🔧 Available Commands:${colors.reset}`);
    log(`\n${colors.yellow}1. Start Backend (Network Ready):${colors.reset}`);
    log(`   cd backend && python main.py`);
    log(`   🌐 Backend will be available at: http://${localIP}:8002`);

    log(`\n${colors.yellow}2. Start Frontend (Network Ready):${colors.reset}`);
    log(`   cd frontend && npm run dev:lan`);
    log(`   🌐 Frontend will be available at: http://${localIP}:5175`);

    log(`\n${colors.yellow}3. Start Frontend with Custom Backend:${colors.reset}`);
    log(`   cd frontend && VITE_BACKEND_HOST=${localIP} npm run dev:custom-backend`);
    log(`   🌐 Frontend: http://${localIP}:5175`);
    log(`   🔗 Backend: http://${localIP}:8002`);

    log(`\n${colors.yellow}4. Full Network Access (Run in separate terminals):${colors.reset}`);
    log(`   Terminal 1: cd backend && python main.py`);
    log(`   Terminal 2: cd frontend && npm run dev:lan`);

    log(`\n${colors.bright}${colors.green}🎯 Quick Start:${colors.reset}`);

    const startBackend = process.argv.includes('--backend');
    const startFrontend = process.argv.includes('--frontend');

    if (startBackend) {
      log(`\n${colors.cyan}🚀 Starting Backend...${colors.reset}`);
      await runCommand('python main.py', backendDir, 'Backend Server');
      log(`\n${colors.green}✅ Backend is running at: http://${localIP}:8002${colors.reset}`);
    }

    if (startFrontend) {
      log(`\n${colors.cyan}🚀 Starting Frontend...${colors.reset}`);
      await runCommand('npm run dev:lan', frontendDir, 'Frontend Server');
      log(`\n${colors.green}✅ Frontend is running at: http://${localIP}:5175${colors.reset}`);
    }

    log(`\n${colors.bright}${colors.green}🎉 Setup Complete!${colors.reset}`);
    log(`\n${colors.cyan}📋 Access URLs:${colors.reset}`);
    log(`   🔗 Backend API: http://${localIP}:8002`);
    log(`   🖥️  Frontend:    http://${localIP}:5175`);
    log(`   📖 API Docs:    http://${localIP}:8002/docs`);

    log(`\n${colors.yellow}💡 Tips:${colors.reset}`);
    log(`   • Make sure Windows Firewall allows ports 8002 & 5175`);
    log(`   • Other devices can access using your IP address`);
    log(`   • Use --backend flag to auto-start backend`);
    log(`   • Use --frontend flag to auto-start frontend`);
    log(`   • Use both flags for full auto-start`);

  } catch (error) {
    log(`\n${colors.red}❌ Setup failed: ${error.message}${colors.reset}`);
    process.exit(1);
  }
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  log(`\n${colors.bright}${colors.blue}🌐 Payroll System Network Setup Help${colors.reset}`);
  log('=' .repeat(50));
  log(`\n${colors.cyan}Usage:${colors.reset}`);
  log(`   node network-setup.js [options]`);
  log(`\n${colors.cyan}Options:${colors.reset}`);
  log(`   --backend     Auto-start backend server`);
  log(`   --frontend    Auto-start frontend server`);
  log(`   --help, -h    Show this help message`);
  log(`\n${colors.cyan}Examples:${colors.reset}`);
  log(`   node network-setup.js                    # Setup only`);
  log(`   node network-setup.js --backend          # Setup + start backend`);
  log(`   node network-setup.js --frontend         # Setup + start frontend`);
  log(`   node network-setup.js --backend --frontend # Setup + start both`);
  process.exit(0);
}

// Run the main function
main().catch(console.error);