# K8s Lambda Shim - Quick Reference

## 🚀 Installation
```bash
pip install -e .
```

## 📋 Common Commands

### Setup
```bash
# Create config
k8s-shim init config.yaml

# Validate config
k8s-shim validate -c config.yaml
```

### Running
```bash
# Start server (default: localhost:8000)
k8s-shim serve -c config.yaml

# Custom host/port
k8s-shim serve -c config.yaml --host 0.0.0.0 --port 9000

# Verbose logging
k8s-shim serve -c config.yaml -v
```

### Testing
```bash
# Test SQS event
k8s-shim invoke -c config.yaml -t sqs -f my-function -p event.json

# Test EventBridge
k8s-shim invoke -c config.yaml -t eventbridge -f my-function -p event.json

# Test API Gateway
k8s-shim invoke -c config.yaml -t api-gateway -f my-function -p event.json

# Direct invoke
k8s-shim invoke -c config.yaml -t direct -f my-function
```

### Kubernetes
```bash
# List services in namespace
k8s-shim list-services -n default
k8s-shim list-services -n freightverify
```

## 🌐 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List services
curl http://localhost:8000/services

# Invoke function
curl -X POST http://localhost:8000/invoke/my-function \
  -H "Content-Type: application/json" \
  -d @event.json

# SQS event
curl -X POST http://localhost:8000/sqs/my-function \
  -H "Content-Type: application/json" \
  -d @sqs-event.json

# EventBridge event
curl -X POST http://localhost:8000/eventbridge/my-function \
  -H "Content-Type: application/json" \
  -d @eventbridge-event.json

# API Gateway event
curl -X POST http://localhost:8000/api-gateway/my-function \
  -H "Content-Type: application/json" \
  -d @api-gateway-event.json
```

## 📝 Config Template

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

## 🐳 Docker

```bash
# Build
docker build -t k8s-lambda-shim .

# Run
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/config/config.yaml \
  k8s-lambda-shim

# Custom command
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/config/config.yaml \
  k8s-lambda-shim validate -c /config/config.yaml
```

## 🔍 Troubleshooting

```bash
# Check services
curl http://localhost:8000/services

# Verbose logging
k8s-shim serve -c config.yaml -v

# Validate config
k8s-shim validate -c config.yaml

# List K8s services
k8s-shim list-services -n your-namespace
```

## 🎯 Event Types

- `sqs` - SQS queue messages
- `eventbridge` - EventBridge events
- `api-gateway` - API Gateway requests
- `direct` - Direct Lambda invocations

## 📦 Event Payload Examples

### SQS Event
```json
{
  "Records": [
    {
      "messageId": "msg-001",
      "body": {
        "data": "your data here"
      }
    }
  ]
}
```

### EventBridge Event
```json
{
  "detail-type": "MyEvent",
  "source": "my.application",
  "detail": {
    "data": "your data here"
  }
}
```

### API Gateway Event
```json
{
  "httpMethod": "POST",
  "body": {
    "data": "your data here"
  }
}
```
