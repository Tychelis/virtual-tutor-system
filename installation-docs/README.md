# Installation Documentation

This folder contains all the installation and configuration documentation for the Virtual Tutor System.

## 📚 Documentation Files

### Core Installation Guides

1. **[INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)** - **START HERE!**
   - Complete system installation and configuration guide
   - Covers all modules: Backend, LLM, RAG, Avatar Manager, Lip-Sync, Frontend
   - Includes system requirements, environment setup, port configuration
   - Contains 10+ troubleshooting scenarios with solutions
   - **Recommended for all users**

### Supporting Documentation

2. **[CONDA_ENVIRONMENTS.md](./CONDA_ENVIRONMENTS.md)**
   - Quick reference for Conda virtual environment setup
   - Details about the 3 required conda environments:
     - `bread` - Backend (Python 3.10)
     - `rag` - RAG & LLM services (Python 3.12)
     - `avatar` - Avatar Manager & Lip-Sync (Python 3.10)
   - One-click setup scripts and verification methods

3. **[DEPENDENCIES.md](./DEPENDENCIES.md)**
   - Project dependencies overview
   - Lists all `requirements.txt` and `package.json` files
   - Organized by module with key dependencies highlighted
   - Useful for understanding what each module requires

4. **[INSTALLATION_VERIFICATION.md](./INSTALLATION_VERIFICATION.md)**
   - Installation verification checklist
   - Lists known issues and improvement suggestions
   - References the verification script: `scripts/verify_installation.sh`
   - Use this to validate your installation

## 🚀 Quick Start

If you're new to this project, follow these steps:

1. **Read the main installation guide**: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)

2. **Set up Conda environments** (refer to [CONDA_ENVIRONMENTS.md](./CONDA_ENVIRONMENTS.md)):
   ```bash
   # Create the 3 required environments
   conda create -n bread python=3.10
   conda create -n rag python=3.12
   conda create -n avatar python=3.10
   ```

3. **Install dependencies** (listed in [DEPENDENCIES.md](./DEPENDENCIES.md)):
   ```bash
   # Install for each module
   conda activate bread && cd backend && pip install -r requirements.txt
   conda activate rag && cd rag && pip install -r requirements.txt
   conda activate rag && cd llm && pip install -r requirements.txt
   conda activate avatar && cd lip-sync && pip install -r requirements.txt
   conda activate avatar && cd avatar-manager && pip install -r requirements.txt
   ```

4. **Verify installation** (using [INSTALLATION_VERIFICATION.md](./INSTALLATION_VERIFICATION.md)):
   ```bash
   # Run the verification script
   bash scripts/verify_installation.sh
   ```

5. **Start the system**:
   ```bash
   # Use the automated startup script
   ./scripts/start_all.sh
   ```

## 📖 Additional Resources

- **Port Configuration**: See [../PORT_CONFIG_GUIDE.md](../PORT_CONFIG_GUIDE.md)
- **Module-Specific READMEs**:
  - Backend: [../backend/README.md](../backend/README.md)
  - LLM: [../llm/README.md](../llm/README.md)
  - RAG: [../rag/README.md](../rag/README.md)
  - Avatar Manager: [../avatar-manager/README.md](../avatar-manager/README.md)
  - Lip-Sync: [../lip-sync/README.md](../lip-sync/README.md)
  - Frontend: [../frontend/README.md](../frontend/README.md)

## ❓ Getting Help

If you encounter issues during installation:

1. Check the **Troubleshooting** section in [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)
2. Review [INSTALLATION_VERIFICATION.md](./INSTALLATION_VERIFICATION.md) for known issues
3. Check service logs in `backend/logs/`, `llm/logs/`, `rag/logs/`
4. Open an issue on GitHub with detailed error messages

---

**Last Updated**: November 22, 2025  
**Maintainer**: Virtual Tutor Development Team
