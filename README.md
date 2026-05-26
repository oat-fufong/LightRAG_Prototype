### Clone Repository
```bas
git clone https://github.com/oat-fufong/LightRAG_Prototype.git
cd LightRAG_Prototype
```
### Local Hosting (No Docker)

* Install UV

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

*  Setup Virtual Environment
```bash
# Initialize the project and create a local venv
uv venv

# Activate virtual environment
source .venv/bin/activate # (Linux/macOS)
# (for Windows) ./.venv/Scripts/activate  
```

* Dependencies Installation & Environment Variables
```bash
# Copy .env template
cp env.poc .env 
# Update the .env, specifically: 
# LLM_BINDING_HOST, LLM_BINDING_API_KEY, LLM_MODEL
# EMBEDDING_BINDING_HOST, EMBEDDING_BINDING_API_KEY, EMBEDDING_MODEL

# Install dependencies
uv sync
```
* Starting LightRAG Server & WebUI
```bash
# Start LightRAG server
uv run lightrag-server
```
### Docker Setup
```bash
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG_Prototype

# Copy .env template
cp env.example .env 
# Update the .env, specifically: 
# LLM_BINDING_HOST, LLM_BINDING_API_KEY, LLM_MODEL
# EMBEDDING_BINDING_HOST, EMBEDDING_BINDING_API_KEY, EMBEDDING_MODEL

docker compose up
```
