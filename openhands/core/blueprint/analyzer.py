import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

class ProjectAnalyzer:
    """Analyzes project structure and generates blueprints."""
    
    FRAMEWORK_PATTERNS = {
        'backend': {
            'express': {
                'files': ['app.js', 'server.js', 'index.js'],
                'dependencies': ['express'],
                'patterns': [
                    r'app\s*=\s*express\(\)',
                    r'router\s*=\s*express\.Router\(\)'
                ]
            },
            'fastify': {
                'files': ['app.js', 'server.js', 'index.js'],
                'dependencies': ['fastify'],
                'patterns': [
                    r'fastify\(\{',
                    r'fastify\.register\('
                ]
            },
            'django': {
                'files': ['manage.py', 'wsgi.py'],
                'dependencies': ['django'],
                'patterns': [
                    r'from django',
                    r'INSTALLED_APPS'
                ]
            },
            'flask': {
                'files': ['app.py', 'wsgi.py'],
                'dependencies': ['flask'],
                'patterns': [
                    r'from flask import',
                    r'Flask\(__name__\)'
                ]
            }
        },
        'frontend': {
            'react': {
                'files': ['App.jsx', 'App.tsx', 'index.jsx', 'index.tsx'],
                'dependencies': ['react', 'react-dom'],
                'patterns': [
                    r'import React',
                    r'from [\'"]react[\'"]'
                ]
            },
            'vue': {
                'files': ['App.vue', 'main.js', 'main.ts'],
                'dependencies': ['vue'],
                'patterns': [
                    r'<template>',
                    r'createApp\('
                ]
            },
            'angular': {
                'files': ['app.module.ts', 'main.ts'],
                'dependencies': ['@angular/core'],
                'patterns': [
                    r'@NgModule\(\{',
                    r'platformBrowserDynamic'
                ]
            }
        },
        'database': {
            'mongoose': {
                'files': ['models/*.js', 'models/*.ts'],
                'dependencies': ['mongoose'],
                'patterns': [
                    r'mongoose\.Schema\(',
                    r'mongoose\.model\('
                ]
            },
            'sequelize': {
                'files': ['models/*.js', 'models/*.ts'],
                'dependencies': ['sequelize'],
                'patterns': [
                    r'extends Model',
                    r'sequelize\.define\('
                ]
            },
            'prisma': {
                'files': ['schema.prisma'],
                'dependencies': ['@prisma/client'],
                'patterns': [
                    r'model \w+ \{',
                    r'provider = ".*"'
                ]
            }
        }
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.frameworks = {
            'backend': None,
            'frontend': None,
            'database': None
        }
        self.db_schemas = {}
        self.api_specs = {}
        self.frontend_components = {}
        self.routes = []
        self.dependencies = {}
        self.documentation = {}
        self.env_vars = {}
        self.dependency_graph = {}

    async def analyze(self) -> Dict[str, Any]:
        """Analyze project and generate blueprint."""
        await self._detect_frameworks()
        await self._find_database_schemas()
        await self._find_api_endpoints()
        await self._find_frontend_components()
        await self._find_dependencies()
        await self._extract_documentation()
        await self._analyze_env_vars()
        await self._build_dependency_graph()

        return self._generate_blueprint()

    async def _detect_frameworks(self):
        """Detect frameworks used in the project."""
        for type_name, frameworks in self.FRAMEWORK_PATTERNS.items():
            for framework_name, patterns in frameworks.items():
                has_files = any(
                    (self.project_path / file_pattern).exists() 
                    for file_pattern in patterns['files']
                )
                
                has_deps = await self._check_dependencies(patterns['dependencies'])
                
                if has_files and has_deps:
                    # Check code patterns
                    for file_pattern in patterns['files']:
                        for file in self.project_path.glob(file_pattern):
                            content = file.read_text()
                            if any(re.search(pattern, content) for pattern in patterns['patterns']):
                                self.frameworks[type_name] = framework_name
                                break

    async def _check_dependencies(self, deps: List[str]) -> bool:
        """Check if project has specified dependencies."""
        package_json = self.project_path / 'package.json'
        requirements_txt = self.project_path / 'requirements.txt'
        
        if package_json.exists():
            with open(package_json) as f:
                pkg = json.load(f)
                all_deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                return all(dep in all_deps for dep in deps)
                
        if requirements_txt.exists():
            with open(requirements_txt) as f:
                reqs = f.read().splitlines()
                return all(any(req.startswith(dep) for req in reqs) for dep in deps)
                
        return False

    async def _find_database_schemas(self):
        """Find and analyze database schemas."""
        for model_file in self.project_path.rglob('models/*.py'):
            content = model_file.read_text()
            # Basic model detection for Django/SQLAlchemy
            model_matches = re.finditer(r'class\s+(\w+)\s*\(.*Model.*\):', content)
            for match in model_matches:
                class_name = match.group(1)
                self.db_schemas[class_name] = {
                    'file': str(model_file.relative_to(self.project_path))
                }

    async def _find_api_endpoints(self):
        """Find API endpoints."""
        for route_file in self.project_path.rglob('**/routes/*.py'):
            content = route_file.read_text()
            # Find Flask/FastAPI route definitions
            route_matches = re.finditer(r'@.*\.(get|post|put|delete)\s*\([\'"]([^\'"]+)[\'"]', content)
            for match in route_matches:
                method, route = match.groups()
                self.api_specs[f"{method.upper()} {route}"] = {
                    'file': str(route_file.relative_to(self.project_path))
                }

    async def _find_frontend_components(self):
        """Find frontend components and routes."""
        for component_file in self.project_path.rglob('**/*.tsx'):
            content = component_file.read_text()
            if 'React' in content or 'export default' in content:
                name = component_file.stem
                self.frontend_components[name] = {
                    'type': 'component',
                    'file': str(component_file.relative_to(self.project_path))
                }
                
                if '<Route' in content or 'useRoutes' in content:
                    self.routes.append(str(component_file.relative_to(self.project_path)))

    async def _find_dependencies(self):
        """Find project dependencies."""
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                pkg = json.load(f)
                self.dependencies['npm'] = {
                    'dependencies': pkg.get('dependencies', {}),
                    'devDependencies': pkg.get('devDependencies', {})
                }

    async def _extract_documentation(self):
        """Extract documentation from markdown files."""
        for doc_file in self.project_path.rglob('*.md'):
            self.documentation[str(doc_file.relative_to(self.project_path))] = doc_file.read_text()

    async def _analyze_env_vars(self):
        """Analyze environment variables."""
        env_files = ['.env', '.env.example', '.env.sample', '.env.development']
        for env_file in env_files:
            env_path = self.project_path / env_file
            if env_path.exists():
                content = env_path.read_text()
                vars = {}
                for line in content.splitlines():
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            vars[key.strip()] = value.strip()
                self.env_vars[env_file] = vars

    async def _build_dependency_graph(self):
        """Build project dependency graph."""
        nodes = []
        edges = []

        # Add framework nodes
        for type_name, framework in self.frameworks.items():
            if framework:
                nodes.append({
                    'id': f'framework_{type_name}',
                    'label': framework,
                    'type': 'framework'
                })

        # Add database nodes
        for schema in self.db_schemas:
            nodes.append({
                'id': f'schema_{schema}',
                'label': schema,
                'type': 'database'
            })

        # Add API nodes
        for endpoint in self.api_specs:
            nodes.append({
                'id': f'api_{endpoint}',
                'label': endpoint,
                'type': 'api'
            })

        # Add frontend nodes
        for component in self.frontend_components:
            nodes.append({
                'id': f'component_{component}',
                'label': component,
                'type': 'frontend'
            })

        self.dependency_graph = {
            'nodes': nodes,
            'edges': edges
        }

    def _generate_blueprint(self) -> Dict[str, Any]:
        """Generate final blueprint."""
        return {
            'project_details': {
                'path': str(self.project_path),
                'analyzed_at': str(Path.ctime(self.project_path)),
                'frameworks': self.frameworks
            },
            'database': {
                'schemas': self.db_schemas
            },
            'api': {
                'endpoints': self.api_specs
            },
            'frontend': {
                'components': self.frontend_components,
                'routes': self.routes
            },
            'dependencies': self.dependencies,
            'documentation': self.documentation,
            'environment': self.env_vars,
            'architecture': self.dependency_graph
        }
