# K8s Lambda Shim - CLI Package

Enhanced Python package with CLI tools for managing and running the K8s Lambda Shim.

## Installation

```bash
# Install in development mode
cd /Users/elliottbregni/dev/k8s-lambda-shim
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## CLI Commands

After installation, the `k8s-shim` command will be available:

### Initialize Configuration

```bash
# Generate a sample config file
k8s-shim init config.yaml

# This creates a template with all configuration options
```

### Validate Configuration

```bash
# Validate your config file
k8s-shim validate -c config.yaml

# Output:
# Configuration is valid
# Services configured: 4
# - asn-processor → freightverify/asn-processor-service:8080
# - parts-validator → freightverify/parts-validator-service:8080
```

### Start Server

```bash
# Start the Lambda shim server
k8s-shim serve -c examples/config.yaml

# Custom host/port
k8s-shim serve -c config.yaml --host 0.0.0.0 --port 9000

# With verbose logging
k8s-shim serve -c config.yaml -v
```

### Test Invocation

```bash
# Invoke a function with a test event
k8s-shim invoke -c config.yaml -t sqs -f asn-processor -p examples/test-sqs-event.json

# Direct invoke without payload file
k8s-shim invoke -c config.yaml -t direct -f parts-validator

# EventBridge event
k8s-shim invoke -c config.yaml -t eventbridge -f shipment-tracker -p event.json
```

### List K8s Services

```bash
# List available services in a namespace
k8s-shim list-services -n freightverify

# Output:
# Services in namespace 'freightverify':
# asn-processor-service
# Type: ClusterIP
# Ports: 8080/TCP
```

## Server API Endpoints

When running the server, the following endpoints are available:

### Health Check
```bash
curl http://localhost:8000/health
```

### Invoke by Function Name
```bash
curl -X POST http://localhost:8000/invoke/asn-processor \
 -H "Content-Type: application/json" \
 -d @examples/test-sqs-event.json
```

### Event-Specific Endpoints
```bash
# SQS events
curl -X POST http://localhost:8000/sqs/asn-processor \
 -H "Content-Type: application/json" \
 -d @sqs-event.json

# EventBridge events
curl -X POST http://localhost:8000/eventbridge/asn-processor \
 -H "Content-Type: application/json" \
 -d @eventbridge-event.json

# API Gateway events
curl -X POST http://localhost:8000/api-gateway/parts-validator \
 -H "Content-Type: application/json" \
 -d @api-gateway-event.json
```

### List Registered Services
```bash
curl http://localhost:8000/services
```

## Configuration Format

### YAML Structure

```yaml
services:
 - name: asn-processor
 namespace: freightverify
 service_name: asn-processor-service
 port: 8080
 path: /process

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

## Usage Examples

### Example 1: Development Testing

```bash
# 1. Create config
k8s-shim init dev-config.yaml

# 2. Edit config with your services
nano dev-config.yaml

# 3. Validate
k8s-shim validate -c dev-config.yaml

# 4. Test invoke
k8s-shim invoke -c dev-config.yaml -t sqs -f my-function -p test-event.json

# 5. Start server
k8s-shim serve -c dev-config.yaml
```

### Example 2: Production Deployment

```bash
# Start server with production config
k8s-shim serve -c /etc/k8s-shim/prod-config.yaml --host 0.0.0.0 --port 8000
```

### Example 3: Kubernetes Deployment

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
 image: your-registry/k8s-lambda-shim:latest
 command: ["k8s-shim", "serve", "-c", "/config/config.yaml"]
 ports:
 - containerPort: 8000
 volumeMounts:
 - name: config
 mountPath: /config
 volumes:
 - name: config
 configMap:
 name: lambda-shim-config
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=shim tests/

# Run specific test
pytest tests/test_cli.py -v
```

## Docker Usage

```bash
# Build image
docker build -t k8s-lambda-shim .

# Run container
docker run -p 8000:8000 -v $(pwd)/config.yaml:/config/config.yaml \
 k8s-lambda-shim serve -c /config/config.yaml
```

## Common Workflows

### Adding a New Service

1. Add to config.yaml:
```yaml
services:
 - name: new-function
 namespace: default
 service_name: new-service
 port: 8080
 path: /handler
```

2. Validate:
```bash
k8s-shim validate -c config.yaml
```

3. Restart server or reload config

### Debugging

```bash
# Enable verbose logging
k8s-shim serve -c config.yaml -v

# Check which services are registered
curl http://localhost:8000/services

# Test with sample payload
k8s-shim invoke -c config.yaml -t direct -f my-function -p test.json
```

## Troubleshooting

**Service not found error:**
```bash
# List available services in namespace
k8s-shim list-services -n your-namespace

# Verify config
k8s-shim validate -c config.yaml
```

**Connection errors:**
- Ensure Kubernetes context is set correctly
- Check service is running: `kubectl get svc -n namespace`
- Verify network policies allow traffic

## License

MIT
