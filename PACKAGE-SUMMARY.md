# K8s Lambda Shim - Python Package Summary

## What Was Created

A complete, production-ready Python package with CLI tools for running and managing your K8s Lambda Shim.

## Package Components

### 1. CLI Tool (`src/shim/cli.py`)
Command-line interface with 5 main commands:
- `init` - Generate sample configuration
- `validate` - Validate configuration files
- `serve` - Start the HTTP server
- `invoke` - Test function invocations
- `list-services` - Browse K8s services

### 2. FastAPI Server (`src/shim/server.py`)
Production HTTP server with:
- Health check endpoint
- Event-type-specific endpoints
- Automatic event type detection
- Service registry integration
- Middleware chain support

### 3. Docker Support (`Dockerfile`)
Container image with:
- Python 3.13 slim base
- Health checks
- Configurable via volume mounts
- Production-ready defaults

### 4. Documentation
- `README.md` - Main project documentation
- `CLI-README.md` - Detailed CLI usage guide
- `QUICK-REFERENCE.md` - Quick command reference

### 5. Examples
- `examples/config.yaml` - Production-ready config
- `examples/test-sqs-event.json` - Sample test payload

## Installation & Usage

### Install Package
```bash
cd /Users/elliottbregni/dev/k8s-lambda-shim
pip install -e .
```

### Quick Start
```bash
# 1. Create config
k8s-shim init my-config.yaml

# 2. Edit config with your services
# 3. Validate
k8s-shim validate -c my-config.yaml

# 4. Start server
k8s-shim serve -c my-config.yaml
```

### Test Invocation
```bash
k8s-shim invoke -c examples/config.yaml \
 -t sqs \
 -f asn-processor \
 -p examples/test-sqs-event.json
```

## Key Features

### CLI Features
 Configuration generation with sensible defaults
 Configuration validation with detailed error messages
 Local testing without deploying
 K8s service discovery
 Verbose logging mode
 Multiple event type support

### Server Features
 Auto-detection of event types
 RESTful API endpoints
 Health checks for K8s
 Service registry management
 Middleware chain execution
 JSON error responses

### DevOps Features
 Docker containerization
 Health check endpoints
 Configurable via YAML
 Volume-mounted configs
 Production-ready logging

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Create sample config | `k8s-shim init config.yaml` |
| `validate` | Validate config | `k8s-shim validate -c config.yaml` |
| `serve` | Start server | `k8s-shim serve -c config.yaml` |
| `invoke` | Test function | `k8s-shim invoke -c config.yaml -t sqs -f my-func -p event.json` |
| `list-services` | List K8s services | `k8s-shim list-services -n default` |

## API Endpoints

When server is running (default: http://localhost:8000):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/services` | GET | List registered services |
| `/invoke/{function}` | POST | Invoke any function |
| `/sqs/{function}` | POST | Handle SQS events |
| `/eventbridge/{function}` | POST | Handle EventBridge events |
| `/api-gateway/{function}` | POST | Handle API Gateway events |

## Docker Usage

### Build Image
```bash
docker build -t k8s-lambda-shim .
```

### Run Container
```bash
docker run -p 8000:8000 \
 -v $(pwd)/examples/config.yaml:/config/config.yaml \
 k8s-lambda-shim
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
 name: lambda-shim
spec:
 replicas: 3
 template:
 spec:
 containers:
 - name: shim
 image: k8s-lambda-shim:latest
 command: ["k8s-shim", "serve", "-c", "/config/config.yaml"]
 ports:
 - containerPort: 8000
 livenessProbe:
 httpGet:
 path: /health
 port: 8000
 initialDelaySeconds: 5
 periodSeconds: 10
 volumeMounts:
 - name: config
 mountPath: /config
 volumes:
 - name: config
 configMap:
 name: lambda-shim-config
```

## Use Cases

### Development
```bash
# Test locally without K8s
k8s-shim invoke -c config.yaml -t direct -f my-func

# Validate changes
k8s-shim validate -c config.yaml
```

### Testing
```bash
# Start local server
k8s-shim serve -c config.yaml

# Send test events
curl -X POST http://localhost:8000/sqs/asn-processor \
 -H "Content-Type: application/json" \
 -d @test-event.json
```

### Production
```bash
# Run as service
k8s-shim serve -c /etc/k8s-shim/prod-config.yaml --host 0.0.0.0

# Or use Docker
docker run -d -p 8000:8000 \
 -v /etc/k8s-shim/config.yaml:/config/config.yaml \
 --name lambda-shim \
 k8s-lambda-shim
```

## Configuration Example

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

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint code
ruff check src/

# Format code
ruff format src/
```

## Next Steps

1. **Customize Configuration**: Edit `examples/config.yaml` with your services
2. **Add Middleware**: Extend with custom middleware for your use case
3. **Deploy to K8s**: Use the example Kubernetes deployment
4. **Monitor**: Use health endpoints for monitoring/alerting
5. **Scale**: Run multiple replicas behind a load balancer

## Package is Ready!

The package is fully functional and ready to use. Run `k8s-shim --help` to get started!

```bash
k8s-shim --help
```
