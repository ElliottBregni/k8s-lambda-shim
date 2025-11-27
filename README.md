# K8s Lambda Shim 🚀

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **Event dispatcher for routing AWS Lambda events to Kubernetes services, eliminating Lambda-to-Lambda invocations.**

Transform your Lambda-heavy AWS architecture into a streamlined K8s-native solution. Route SQS, EventBridge, and API Gateway events directly to your Kubernetes services without the Lambda overhead.

---

## ✨ Features

- 🎯 **Multi-source event handling**: API Gateway, EventBridge, SQS, Direct Invoke
- 📦 **Service Registry**: Maps Lambda function names to K8s service endpoints
- 🔗 **Middleware Chain**: Auth, logging, validation (fully extensible)
- 🛡️ **Type-safe**: Full Pydantic models and type hints
- ⚡ **CLI Tool**: Easy management and testing with `k8s-shim` command
- 🌐 **REST API**: Production-ready HTTP server
- 🐳 **Docker Ready**: Container image with health checks
- 📊 **Observable**: Built-in logging and health endpoints

## 🏗️ Architecture

```
┌─────────────────┐
│  AWS Event      │
│  Sources        │
│  • SQS          │
│  • EventBridge  │
│  • API Gateway  │
│  • Direct       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Event          │
│  Dispatcher     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Middleware     │
│  Chain          │
│  • Logging      │
│  • Validation   │
│  • Auth         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Service        │
│  Registry       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kubernetes     │
│  Service        │
└─────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repo
git clone https://github.com/ElliottBregni/k8s-lambda-shim.git
cd k8s-lambda-shim

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

**Server will be running at:** `http://localhost:8000`

## 📦 CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Generate sample config | `k8s-shim init config.yaml` |
| `validate` | Validate configuration | `k8s-shim validate -c config.yaml` |
| `serve` | Start HTTP server | `k8s-shim serve -c config.yaml` |
| `invoke` | Test function invocation | `k8s-shim invoke -c config.yaml -t sqs -f my-func -p event.json` |
| `list-services` | List K8s services | `k8s-shim list-services -n default` |

**See [CLI-README.md](CLI-README.md) for detailed CLI documentation.**

## 🌐 API Endpoints

Once the server is running:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/services` | GET | List registered services |
| `/invoke/{function}` | POST | Invoke any function (auto-detects event type) |
| `/sqs/{function}` | POST | Handle SQS events |
| `/eventbridge/{function}` | POST | Handle EventBridge events |
| `/api-gateway/{function}` | POST | Handle API Gateway events |

### Example Requests

```bash
# Health check
curl http://localhost:8000/health

# List services
curl http://localhost:8000/services

# Invoke function with SQS event
curl -X POST http://localhost:8000/sqs/asn-processor \
  -H "Content-Type: application/json" \
  -d @examples/test-sqs-event.json
```

## ⚙️ Configuration

### YAML Configuration

```yaml
services:
  - name: asn-processor
    namespace: freightverify
    service_name: asn-processor-service
    port: 8080
    path: /process
  
  - name: parts-validator
    namespace: freightverify
    service_name: parts-validator-service
    port: 8080
    path: /validate

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

### Python Configuration

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

## 🐳 Docker Usage

### Build Image

```bash
docker build -t k8s-lambda-shim .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/config/config.yaml \
  k8s-lambda-shim
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lambda-shim
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lambda-shim
  template:
    metadata:
      labels:
        app: lambda-shim
    spec:
      containers:
      - name: shim
        image: k8s-lambda-shim:latest
        command: ["k8s-shim", "serve", "-c", "/config/config.yaml"]
        ports:
        - containerPort: 8000
          name: http
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 3
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /config
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: lambda-shim-config
---
apiVersion: v1
kind: Service
metadata:
  name: lambda-shim
  namespace: default
spec:
  selector:
    app: lambda-shim
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
```

## 🔧 Middleware

Chain middleware for cross-cutting concerns:

```python
from shim.middleware import MiddlewareChain, LoggingMiddleware, ValidationMiddleware

chain = MiddlewareChain([
    LoggingMiddleware(),
    ValidationMiddleware(),
])
```

### Custom Middleware

```python
from shim.middleware.base import Middleware
from shim.events.dispatcher import Event

class CustomMiddleware(Middleware):
    async def process(self, event: Event, next_handler):
        # Pre-processing
        print(f"Processing {event.function_name}")
        
        # Call next middleware
        result = await next_handler(event)
        
        # Post-processing
        print(f"Completed {event.function_name}")
        return result
```

## 📚 Examples

See the `examples/` directory for complete examples:

- **`asn_processor.py`** - ASN processing with multiple event types
- **`config.yaml`** - Production-ready configuration
- **`test-sqs-event.json`** - Sample test event payload

### Running Examples

```bash
# Start server with example config
k8s-shim serve -c examples/config.yaml

# Test with sample event
k8s-shim invoke -c examples/config.yaml \
  -t sqs \
  -f asn-processor \
  -p examples/test-sqs-event.json
```

## 🧪 Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=shim tests/

# Run specific test
pytest tests/test_dispatcher.py -v
```

### Linting

```bash
# Check code
ruff check src/

# Format code
ruff format src/
```

## 📖 Documentation

- **[README.md](README.md)** - This file (main documentation)
- **[CLI-README.md](CLI-README.md)** - Detailed CLI usage guide
- **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** - Command cheat sheet
- **[PACKAGE-SUMMARY.md](PACKAGE-SUMMARY.md)** - Complete package overview

## 🎯 Use Cases

### Development & Testing

```bash
# Test locally without K8s
k8s-shim invoke -c config.yaml -t direct -f my-func

# Validate configuration changes
k8s-shim validate -c config.yaml
```

### Production Deployment

```bash
# Run as systemd service
k8s-shim serve -c /etc/k8s-shim/prod-config.yaml --host 0.0.0.0

# Or use Docker
docker run -d -p 8000:8000 \
  -v /etc/k8s-shim/config.yaml:/config/config.yaml \
  --name lambda-shim \
  --restart unless-stopped \
  k8s-lambda-shim
```

### CI/CD Integration

```bash
# Validate in CI pipeline
k8s-shim validate -c config.yaml || exit 1

# Deploy to K8s
kubectl apply -f k8s/deployment.yaml
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Click](https://click.palletsprojects.com/) - CLI framework
- [httpx](https://www.python-httpx.org/) - HTTP client

---

<div align="center">

**Made with ❤️ for Kubernetes and AWS**

[Report Bug](https://github.com/ElliottBregni/k8s-lambda-shim/issues) · [Request Feature](https://github.com/ElliottBregni/k8s-lambda-shim/issues)

</div>
