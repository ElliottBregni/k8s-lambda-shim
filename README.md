# K8s Lambda Shim

Event dispatcher for routing AWS Lambda events to Kubernetes services, eliminating Lambda-to-Lambda invocations.

## Features

- **Multi-source event handling**: API Gateway, EventBridge, SQS, Direct Invoke
- **Service Registry**: Maps Lambda function names to K8s service endpoints
- **Middleware Chain**: Auth, logging, validation (extensible)
- **Type-safe**: Full Pydantic models and type hints
- **CLI Tool**: Easy management and testing with `k8s-shim` command
- **REST API**: HTTP server for event handling
- **Docker Ready**: Container image with health checks

## Architecture

```
AWS Event Sources → Event Dispatcher → Middleware Chain → K8s Service Registry → K8s Service
```

## 🚀 Quick Start

### Installation

```bash
# Install package
pip install -e .

# Verify installation
k8s-shim --help
```

### Basic Usage

```bash
# 1. Generate config
k8s-shim init config.yaml

# 2. Configure your services (edit config.yaml)
# 3. Validate config
k8s-shim validate -c config.yaml

# 4. Start server
k8s-shim serve -c config.yaml
```

## 📦 CLI Commands

### Initialize Configuration
```bash
k8s-shim init config.yaml
```

### Validate Configuration
```bash
k8s-shim validate -c config.yaml
```

### Start Server
```bash
k8s-shim serve -c config.yaml --host 0.0.0.0 --port 8000
```

### Test Invocation
```bash
k8s-shim invoke -c config.yaml -t sqs -f asn-processor -p test-event.json
```

### List K8s Services
```bash
k8s-shim list-services -n default
```

See [CLI-README.md](CLI-README.md) for detailed CLI documentation.

## 🐳 Docker Usage

```bash
# Build image
docker build -t k8s-lambda-shim .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/config/config.yaml \
  k8s-lambda-shim
```

## 🌐 API Endpoints

Once the server is running:

- `GET /health` - Health check
- `POST /invoke/{function_name}` - Invoke any function
- `POST /sqs/{function_name}` - Handle SQS events
- `POST /eventbridge/{function_name}` - Handle EventBridge events
- `POST /api-gateway/{function_name}` - Handle API Gateway events
- `GET /services` - List registered services

## Configuration

Register services in the service registry:

```python
from shim.registry.service_registry import ServiceRegistry, ServiceEndpoint

registry = ServiceRegistry()
registry.register("my-function", ServiceEndpoint(
    namespace="default",
    service_name="my-service",
    port=8080,
    path="/invoke"
))
```

### YAML Configuration

```yaml
services:
  - name: my-function
    namespace: default
    service_name: my-service
    port: 8080
    path: /invoke

middleware:
  logging:
    enabled: true
    level: INFO
  validation:
    enabled: true

server:
  host: 0.0.0.0
  port: 8000
  timeout: 30
```

## Middleware

Chain middleware for cross-cutting concerns:

```python
from shim.middleware import MiddlewareChain, LoggingMiddleware, ValidationMiddleware

chain = MiddlewareChain([
    LoggingMiddleware(),
    ValidationMiddleware(),
])
```

## 📚 Examples

See the `examples/` directory for complete examples:
- `asn_processor.py` - ASN processing with multiple event types
- `config.yaml` - Sample configuration
- `test-sqs-event.json` - Test event payload

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/
```

## 📝 License

MIT
