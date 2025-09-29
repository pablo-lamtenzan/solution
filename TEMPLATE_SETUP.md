# Template Setup Guide

This guide helps you customize this Python project template for your specific needs.

## Quick Setup Checklist

- [ ] Update project metadata in `pyproject.toml`
- [ ] Add your dependencies
- [ ] Create source code structure
- [ ] Customize Docker configuration
- [ ] Update README.md with your project details
- [ ] Add your custom invoke tasks

## 1. Project Metadata

Edit `pyproject.toml`:

```toml
[project]
name = "your-project-name"  # Replace with your project name
version = "0.1.0"
description = "Your project description"  # Replace with your description
authors = [
    { name = "Your Name", email = "your.email@example.com" }  # Replace with your info
]
```

## 2. Dependencies

Add your project dependencies:

```toml
dependencies = [
    "requests>=2.31.0",      # Example: HTTP client
    "pydantic>=2.0.0",       # Example: Data validation
    "fastapi>=0.100.0",      # Example: Web framework
    # Add your dependencies here
]
```

For type checking, add corresponding type stubs:

```toml
[dependency-groups]
dev = [
    "invoke>=2.2.0",
    "mypy>=1.17.1",
    "pytest>=8.4.1",
    "ruff>=0.12.11",
    "types-requests>=2.31.0",  # Type stubs for requests
    # Add type stubs for your dependencies
]
```

## 3. Source Code Structure

Create your package structure:

```bash
mkdir -p src/your_package_name
touch src/your_package_name/__init__.py
touch src/your_package_name/main.py

mkdir -p tests
touch tests/__init__.py
touch tests/test_main.py
```

## 4. CLI Scripts (Optional)

If your project has CLI commands, add them to `pyproject.toml`:

```toml
[project.scripts]
your-cli = "your_package.cli:main"
your-tool = "your_package.tools:run"
```

## 5. Docker Configuration

### Basic Web Application

For a web application (FastAPI, Flask, etc.):

```dockerfile
# In Dockerfile, replace the CMD line:
CMD ["uv", "run", "uvicorn", "your_package.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# In docker-compose.yml:
ports:
  - "8000:8000"
```

### Streamlit Application

For a Streamlit app:

```dockerfile
# In Dockerfile:
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "your_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

```yaml
# In docker-compose.yml:
ports:
  - "8501:8501"
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
```

### CLI Application

For a CLI-only application:

```dockerfile
# In Dockerfile:
CMD ["uv", "run", "your-package", "--help"]
```

## 6. Custom Tasks

Add project-specific tasks to `tasks.py`:

```python
@task
def serve(c):
    """Start the development server."""
    c.run("uv run uvicorn your_package.main:app --reload")

@task
def migrate(c):
    """Run database migrations."""
    c.run("uv run alembic upgrade head")

@task
def seed(c):
    """Seed the database with test data."""
    c.run("uv run python -m your_package.seed")
```

## 7. Environment Variables

Add environment variables to `docker-compose.yml`:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - DATABASE_URL=postgresql://user:pass@db:5432/mydb
  - API_KEY=${API_KEY}  # From .env file
  - DEBUG=true
```

## 8. Database Setup (Optional)

Uncomment and customize the database service in `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: your_db_name
      POSTGRES_USER: your_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

volumes:
  postgres_data:
```

## 9. Testing Configuration

The template includes pytest configuration. Customize in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --cov=src --cov-report=term-missing"
```

## 10. Final Steps

1. **Test the setup**:
   ```bash
   uv sync --dev
   uv run invoke check
   ```

2. **Update README.md** with your project-specific information

3. **Initialize git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit from Python template"
   ```

4. **Delete this file** when you're done:
   ```bash
   rm TEMPLATE_SETUP.md
   ```

## Common Project Types

### FastAPI Web API
- Dependencies: `fastapi`, `uvicorn`, `pydantic`
- Docker CMD: `uvicorn your_package.main:app --host 0.0.0.0 --port 8000`
- Port: 8000

### Streamlit Dashboard
- Dependencies: `streamlit`, `pandas`, `plotly`
- Docker CMD: `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`
- Port: 8501

### CLI Tool
- Dependencies: `click` or `typer`
- Scripts: Define in `[project.scripts]`
- Docker: Not typically needed

### Data Science Project
- Dependencies: `pandas`, `numpy`, `matplotlib`, `jupyter`
- Structure: Add `notebooks/` directory
- Tasks: Add data processing and analysis tasks

### Machine Learning Project
- Dependencies: `scikit-learn`, `torch`, `transformers`
- Structure: Add `models/`, `data/` directories
- Tasks: Add training, evaluation, inference tasks
