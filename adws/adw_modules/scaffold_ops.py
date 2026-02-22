"""Project scaffolding operations for Build OS.

Generates the full-stack project structure from templates,
configures design tokens, and initializes the output project.
"""

import json
import logging
import os
import shutil
from typing import Optional, Tuple

from .data_types import DesignSystem, TechStack
from .stack_registry import get_backend_spec, get_frontend_spec
from .utils import get_project_root


def scaffold_project(
    product_name: str,
    tech_stack: TechStack,
    design_system: DesignSystem,
    sections: list,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate the full-stack project structure.

    Args:
        product_name: Name of the product (used for directory name)
        tech_stack: Tech stack configuration
        design_system: Design system tokens
        sections: List of section IDs
        logger: Logger instance

    Returns:
        Tuple of (output_path, error_message)
    """
    project_root = get_project_root()
    slug = product_name.lower().replace(" ", "-")
    output_path = os.path.join(project_root, "output", slug)

    if os.path.exists(output_path):
        logger.warning(f"Output directory already exists: {output_path}")
        return output_path, None

    try:
        # Create the project structure
        _create_directory_structure(output_path, sections, logger)

        # Copy and configure frontend template
        _scaffold_frontend(output_path, product_name, tech_stack, design_system, sections, logger)

        # Copy and configure backend template
        _scaffold_backend(output_path, product_name, tech_stack, sections, logger)

        # Create scripts
        _create_scripts(output_path, logger)

        # Create config files
        _create_config_files(output_path, product_name, tech_stack, logger)

        logger.info(f"Scaffolded project at {output_path}")
        return output_path, None

    except Exception as e:
        error_msg = f"Failed to scaffold project: {e}"
        logger.error(error_msg)
        return None, error_msg


def _create_directory_structure(output_path: str, sections: list, logger: logging.Logger) -> None:
    """Create the full directory tree."""
    dirs = [
        "app/client/src/components",
        "app/client/src/shell",
        "app/client/src/api",
        "app/client/src/types",
        "app/server/routes",
        "app/server/models",
        "app/server/core",
        "app/server/tests",
        "scripts",
    ]

    # Add per-section directories
    for section_id in sections:
        dirs.append(f"app/client/src/sections/{section_id}")

    for d in dirs:
        os.makedirs(os.path.join(output_path, d), exist_ok=True)

    logger.info("Created directory structure")


def _scaffold_frontend(
    output_path: str,
    product_name: str,
    tech_stack: TechStack,
    design_system: DesignSystem,
    sections: list,
    logger: logging.Logger,
) -> None:
    """Scaffold frontend: custom template (templates/frontend/{id}/), built-in generator (react-vite, react-cra), or default template."""
    project_root = get_project_root()
    client_dir = os.path.join(output_path, "app", "client")
    frontend_id = getattr(tech_stack, "frontend", "react-vite") or "react-vite"

    # 1) Custom or registered template path
    spec = get_frontend_spec(frontend_id)
    template_dir = None
    if spec and spec.get("template_path"):
        template_dir = os.path.join(project_root, spec["template_path"])
    if not template_dir or not os.path.isdir(template_dir):
        template_dir = os.path.join(project_root, "templates", "frontend", frontend_id)
    if os.path.isdir(template_dir):
        for item in os.listdir(template_dir):
            src = os.path.join(template_dir, item)
            dst = os.path.join(client_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.info(f"Scaffolded frontend from template: {frontend_id}")
        return

    # 2) Built-in generator for known stacks
    if frontend_id in ("react-vite", "react-cra"):
        _generate_frontend_files(client_dir, product_name, tech_stack, design_system, sections)
        logger.info("Scaffolded frontend")
        return

    # 3) Default template
    default_dir = os.path.join(project_root, "templates", "frontend")
    if os.path.isdir(default_dir):
        for item in os.listdir(default_dir):
            src = os.path.join(default_dir, item)
            dst = os.path.join(client_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.info("Scaffolded frontend from default template")
        return

    # 4) Fallback: generate react-vite
    _generate_frontend_files(client_dir, product_name, tech_stack, design_system, sections)
    logger.info("Scaffolded frontend")


def _generate_frontend_files(
    client_dir: str,
    product_name: str,
    tech_stack: TechStack,
    design_system: DesignSystem,
    sections: list,
) -> None:
    """Generate frontend boilerplate files directly. Branches on tech_stack.frontend (react-vite | react-cra)."""
    is_vite = tech_stack.frontend == "react-vite"

    # package.json — scripts and devDependencies depend on frontend choice
    if is_vite:
        package_json = {
            "name": product_name.lower().replace(" ", "-") + "-client",
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
                "lint": "eslint src/",
            },
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "react-router-dom": "^6.28.0",
                "lucide-react": "^0.460.0",
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.3.4",
                "vite": "^6.0.0",
                "tailwindcss": "^3.4.0",
                "postcss": "^8.4.0",
                "autoprefixer": "^10.4.0",
                "eslint": "^8.56.0",
            },
        }
    else:
        # react-cra
        package_json = {
            "name": product_name.lower().replace(" ", "-") + "-client",
            "private": True,
            "version": "0.1.0",
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "react-router-dom": "^6.28.0",
                "react-scripts": "5.0.1",
                "lucide-react": "^0.460.0",
            },
            "devDependencies": {
                "tailwindcss": "^3.4.0",
                "postcss": "^8.4.0",
                "autoprefixer": "^10.4.0",
                "eslint": "^8.56.0",
            },
            "browserslist": {"production": [">0.2%", "not dead"], "development": ["last 1 chrome version"]},
        }
        package_json["scripts"] = {
            "start": "react-scripts start",
            "dev": "react-scripts start",
            "build": "react-scripts build",
            "lint": "eslint src/",
        }
    with open(os.path.join(client_dir, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)

    if is_vite:
        # vite.config.js (Vite only)
        vite_config = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '3000'),
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
"""
        with open(os.path.join(client_dir, "vite.config.js"), "w") as f:
            f.write(vite_config)

    # tailwind.config.js — content paths and export style differ (Vite: ESM, CRA: CommonJS)
    if is_vite:
        content_paths = "['./index.html', './src/**/*.{js,jsx}']"
        tailwind_config = f"""/** @type {{import('tailwindcss').Config}} */
export default {{
  content: {content_paths},
  theme: {{
    extend: {{
      colors: {{
        primary: require('tailwindcss/colors').{design_system.primary},
        secondary: require('tailwindcss/colors').{design_system.secondary},
        neutral: require('tailwindcss/colors').{design_system.neutral},
      }},
      fontFamily: {{
        heading: ['{design_system.fonts.get("heading", "Inter")}', 'sans-serif'],
        body: ['{design_system.fonts.get("body", "Inter")}', 'sans-serif'],
        mono: ['{design_system.fonts.get("mono", "JetBrains Mono")}', 'monospace'],
      }},
    }},
  }},
  plugins: [],
}};
"""
    else:
        content_paths = "['./src/**/*.{js,jsx}']"
        tailwind_config = f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: {content_paths},
  theme: {{
    extend: {{
      colors: {{
        primary: require('tailwindcss/colors').{design_system.primary},
        secondary: require('tailwindcss/colors').{design_system.secondary},
        neutral: require('tailwindcss/colors').{design_system.neutral},
      }},
      fontFamily: {{
        heading: ['{design_system.fonts.get("heading", "Inter")}', 'sans-serif'],
        body: ['{design_system.fonts.get("body", "Inter")}', 'sans-serif'],
        mono: ['{design_system.fonts.get("mono", "JetBrains Mono")}', 'monospace'],
      }},
    }},
  }},
  plugins: [],
}};
"""
    with open(os.path.join(client_dir, "tailwind.config.js"), "w") as f:
        f.write(tailwind_config)

    # postcss.config.js (CRA expects module.exports for Tailwind)
    if is_vite:
        postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
    else:
        postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
    with open(os.path.join(client_dir, "postcss.config.js"), "w") as f:
        f.write(postcss_config)

    heading_font = design_system.fonts.get("heading", "Inter")
    body_font = design_system.fonts.get("body", "Inter")
    mono_font = design_system.fonts.get("mono", "JetBrains Mono")
    fonts_param = "+".join(sorted(set([heading_font, body_font, mono_font]))).replace(" ", "+")

    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{product_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family={fonts_param}:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""
    if is_vite:
        index_html_vite = index_html_content.rstrip().removesuffix("</body>").removesuffix("</html>")
        index_html_vite += "    <script type=\"module\" src=\"/src/main.jsx\"></script>\n  </body>\n</html>\n"
        with open(os.path.join(client_dir, "index.html"), "w") as f:
            f.write(index_html_vite)
    else:
        # CRA: index.html in public/
        os.makedirs(os.path.join(client_dir, "public"), exist_ok=True)
        with open(os.path.join(client_dir, "public", "index.html"), "w") as f:
            f.write(index_html_content)

    # Entry file: main.jsx (Vite) or src/index.js (CRA)
    entry_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
"""
    os.makedirs(os.path.join(client_dir, "src"), exist_ok=True)
    if is_vite:
        with open(os.path.join(client_dir, "src", "main.jsx"), "w") as f:
            f.write(entry_js)
    else:
        with open(os.path.join(client_dir, "src", "index.js"), "w") as f:
            f.write(entry_js)

    # src/index.css
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    with open(os.path.join(client_dir, "src", "index.css"), "w") as f:
        f.write(index_css)

    # src/App.jsx with routes for all sections
    route_imports = ""
    route_elements = ""
    for section_id in sections:
        component_name = section_id.replace("-", " ").title().replace(" ", "")
        route_imports += f"import {component_name}Page from './sections/{section_id}/{component_name}Page';\n"
        route_elements += f'          <Route path="/{section_id}" element={{<{component_name}Page />}} />\n'

    app_jsx = f"""import {{ Routes, Route }} from 'react-router-dom';
import AppShell from './shell/AppShell';
{route_imports}
function App() {{
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={{<div className="p-6"><h1 className="text-2xl font-heading font-bold">Welcome</h1></div>}} />
{route_elements}      </Routes>
    </AppShell>
  );
}}

export default App;
"""
    with open(os.path.join(client_dir, "src", "App.jsx"), "w") as f:
        f.write(app_jsx)

    # src/shell/AppShell.jsx (placeholder)
    shell_jsx = """function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="flex">
        <nav className="w-64 bg-white border-r border-neutral-200 min-h-screen p-4">
          <div className="text-lg font-heading font-bold text-primary-600 mb-8">
            App
          </div>
          {/* Navigation will be built in build-shell step */}
        </nav>
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppShell;
"""
    os.makedirs(os.path.join(client_dir, "src", "shell"), exist_ok=True)
    with open(os.path.join(client_dir, "src", "shell", "AppShell.jsx"), "w") as f:
        f.write(shell_jsx)


def _scaffold_backend(
    output_path: str,
    product_name: str,
    tech_stack: TechStack,
    sections: list,
    logger: logging.Logger,
) -> None:
    """Scaffold backend: custom template (templates/backend/{id}/), built-in (fastapi), or default template."""
    project_root = get_project_root()
    server_dir = os.path.join(output_path, "app", "server")
    backend_id = getattr(tech_stack, "backend", "fastapi") or "fastapi"

    # 1) Custom or registered template path
    spec = get_backend_spec(backend_id)
    template_dir = None
    if spec and spec.get("template_path"):
        template_dir = os.path.join(project_root, spec["template_path"])
    if not template_dir or not os.path.isdir(template_dir):
        template_dir = os.path.join(project_root, "templates", "backend", backend_id)
    if os.path.isdir(template_dir):
        for item in os.listdir(template_dir):
            src = os.path.join(template_dir, item)
            dst = os.path.join(server_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.info(f"Scaffolded backend from template: {backend_id}")
        return

    # 2) Built-in generator for FastAPI
    if backend_id == "fastapi":
        _generate_backend_files(server_dir, product_name, tech_stack, sections)
        logger.info("Scaffolded backend")
        return

    # 3) Default template
    default_dir = os.path.join(project_root, "templates", "backend")
    if os.path.isdir(default_dir):
        for item in os.listdir(default_dir):
            src = os.path.join(default_dir, item)
            dst = os.path.join(server_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.info("Scaffolded backend from default template")
        return

    # 4) Fallback: generate FastAPI
    _generate_backend_files(server_dir, product_name, tech_stack, sections)
    logger.info("Scaffolded backend")


def _generate_backend_files(
    server_dir: str, product_name: str, tech_stack: TechStack, sections: list
) -> None:
    """Generate backend boilerplate files directly. Branches on tech_stack.backend and tech_stack.database."""
    slug = product_name.lower().replace(" ", "-")
    db_choice = tech_stack.database

    # pyproject.toml — database deps depend on tech_stack.database
    base_deps = [
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
    ]
    if db_choice == "sqlite":
        base_deps.append("sqlalchemy>=2.0.0")
    elif db_choice == "postgres":
        base_deps.extend(["sqlalchemy>=2.0.0", "psycopg2-binary>=2.9.0"])

    deps_str = ",\n    ".join(f'"{d}"' for d in base_deps)
    pyproject = f"""[project]
name = "{slug}-server"
version = "0.1.0"
description = "{product_name} API Server"
requires-python = ">=3.10"
dependencies = [
    {deps_str},
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "ruff>=0.1.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py310"
"""
    with open(os.path.join(server_dir, "pyproject.toml"), "w") as f:
        f.write(pyproject)

    # server.py
    server_py = """\"\"\"FastAPI server entry point.\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{title}", version="0.1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {{"status": "healthy"}}


# Route registration — routes are added by build-api step
""".format(title=product_name)
    with open(os.path.join(server_dir, "server.py"), "w") as f:
        f.write(server_py)

    # core/database.py — branch on tech_stack.database
    if db_choice == "sqlite":
        database_py = """\"\"\"Database configuration (SQLite).\"\"\"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
    elif db_choice == "postgres":
        database_py = """\"\"\"Database configuration (PostgreSQL).\"\"\"

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/app")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
    else:
        # none — minimal stub so imports from core.database don't break
        database_py = """\"\"\"No database configured (tech_stack.database = \"none\").\"\"\"

def get_db():
    yield None
"""
    with open(os.path.join(server_dir, "core", "database.py"), "w") as f:
        f.write(database_py)

    # Empty __init__.py files
    for subdir in ["models", "routes", "core"]:
        init_path = os.path.join(server_dir, subdir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                pass

    # tests/conftest.py
    conftest = """\"\"\"Test fixtures for API tests.\"\"\"

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)
"""
    with open(os.path.join(server_dir, "tests", "conftest.py"), "w") as f:
        f.write(conftest)

    with open(os.path.join(server_dir, "tests", "__init__.py"), "w") as f:
        pass


def _create_scripts(output_path: str, logger: logging.Logger) -> None:
    """Create start/stop scripts."""
    scripts_dir = os.path.join(output_path, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    # start.sh
    start_sh = """#!/bin/bash
# Start both frontend and backend services

# Load port configuration
if [ -f .ports.env ]; then
  source .ports.env
fi

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

echo "Starting backend on port $BACKEND_PORT..."
cd app/server && uv run uvicorn server:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
BACKEND_PID=$!

echo "Starting frontend on port $FRONTEND_PORT..."
cd app/client && FRONTEND_PORT=$FRONTEND_PORT npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID (port $BACKEND_PORT)"
echo "Frontend PID: $FRONTEND_PID (port $FRONTEND_PORT)"

# Save PIDs for stop script
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

wait
"""
    start_path = os.path.join(scripts_dir, "start.sh")
    with open(start_path, "w") as f:
        f.write(start_sh)
    os.chmod(start_path, 0o755)

    # stop.sh
    stop_sh = """#!/bin/bash
# Stop both frontend and backend services

if [ -f .backend.pid ]; then
  kill $(cat .backend.pid) 2>/dev/null
  rm .backend.pid
  echo "Stopped backend"
fi

if [ -f .frontend.pid ]; then
  kill $(cat .frontend.pid) 2>/dev/null
  rm .frontend.pid
  echo "Stopped frontend"
fi
"""
    stop_path = os.path.join(scripts_dir, "stop.sh")
    with open(stop_path, "w") as f:
        f.write(stop_sh)
    os.chmod(stop_path, 0o755)

    logger.info("Created start/stop scripts")


def _create_config_files(
    output_path: str, product_name: str, tech_stack: TechStack, logger: logging.Logger
) -> None:
    """Create project config files. DATABASE_URL in .env.sample depends on tech_stack.database."""
    # .ports.env
    with open(os.path.join(output_path, ".ports.env"), "w") as f:
        f.write("BACKEND_PORT=8000\nFRONTEND_PORT=3000\n")

    # .env.sample — branch on database choice
    if tech_stack.database == "sqlite":
        env_sample = "# Environment configuration\nDATABASE_URL=sqlite:///./data.db\n"
    elif tech_stack.database == "postgres":
        env_sample = "# Environment configuration\nDATABASE_URL=postgresql://user:pass@localhost:5432/dbname\n"
    else:
        env_sample = "# Environment configuration (no database)\n"
    with open(os.path.join(output_path, ".env.sample"), "w") as f:
        f.write(env_sample)

    # README.md
    readme = f"""# {product_name}

Built with [Build OS](https://github.com/maitrikpatel2025/agent-hq/tree/main/build-os).

## Setup

### Backend
```bash
cd app/server
uv sync
uv run uvicorn server:app --reload
```

### Frontend
```bash
cd app/client
npm install
npm run dev
```

### Both (via scripts)
```bash
./scripts/start.sh
```
"""
    with open(os.path.join(output_path, "README.md"), "w") as f:
        f.write(readme)

    # .gitignore
    gitignore = """node_modules/
dist/
.env
*.pyc
__pycache__/
*.db
.backend.pid
.frontend.pid
"""
    with open(os.path.join(output_path, ".gitignore"), "w") as f:
        f.write(gitignore)

    logger.info("Created config files")
