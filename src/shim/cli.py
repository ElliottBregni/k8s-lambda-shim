"""CLI tool for K8s Lambda Shim."""
import asyncio
import click
import logging
import yaml
from pathlib import Path
from typing import Optional

from shim.events.dispatcher import EventDispatcher, Event, EventType
from shim.registry.service_registry import ServiceRegistry, ServiceEndpoint
from shim.middleware.base import MiddlewareChain
from shim.middleware.common import LoggingMiddleware, ValidationMiddleware
from shim.handlers import (
 APIGatewayHandler,
 EventBridgeHandler,
 SQSHandler,
 DirectInvokeHandler
)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose: bool):
 """K8s Lambda Shim - Route AWS Lambda events to Kubernetes services."""
 level = logging.DEBUG if verbose else logging.INFO
 logging.basicConfig(
 level=level,
 format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
 )

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), required=True,
 help='Path to configuration YAML file')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to listen on')
def serve(config: str, host: str, port: int):
 """Start the Lambda shim server."""
 import uvicorn
 from .server import create_app

 # Load config
 with open(config) as f:
 cfg = yaml.safe_load(f)

 # Create FastAPI app with config
 app = create_app(cfg)

 click.echo(f" Starting K8s Lambda Shim server on {host}:{port}")
 uvicorn.run(app, host=host, port=port)

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), required=True,
 help='Path to configuration YAML file')
@click.option('--event-type', '-t',
 type=click.Choice(['sqs', 'eventbridge', 'api-gateway', 'direct']),
 required=True, help='Event type')
@click.option('--function', '-f', required=True, help='Target function name')
@click.option('--payload', '-p', type=click.Path(exists=True),
 help='Path to JSON payload file')
def invoke(config: str, event_type: str, function: str, payload: Optional[str]):
 """Invoke a function with a test event."""
 import json

 # Load config
 with open(config) as f:
 cfg = yaml.safe_load(f)

 # Load payload
 event_payload = {}
 if payload:
 with open(payload) as f:
 event_payload = json.load(f)

 # Map event type
 type_map = {
 'sqs': EventType.SQS,
 'eventbridge': EventType.EVENTBRIDGE,
 'api-gateway': EventType.API_GATEWAY,
 'direct': EventType.DIRECT_INVOKE
 }

 async def run():
 # Setup registry
 registry = ServiceRegistry()
 for svc in cfg.get('services', []):
 registry.register(
 svc['name'],
 ServiceEndpoint(
 namespace=svc['namespace'],
 service_name=svc['service_name'],
 port=svc['port'],
 path=svc.get('path', '/')
 )
 )

 # Setup dispatcher
 dispatcher = EventDispatcher()
 dispatcher.register_handler(EventType.API_GATEWAY, APIGatewayHandler(registry))
 dispatcher.register_handler(EventType.EVENTBRIDGE, EventBridgeHandler(registry))
 dispatcher.register_handler(EventType.SQS, SQSHandler(registry))
 dispatcher.register_handler(EventType.DIRECT_INVOKE, DirectInvokeHandler(registry))

 # Setup middleware
 middleware = MiddlewareChain([
 LoggingMiddleware(),
 ValidationMiddleware(),
 ])

 # Create event
 event = Event(
 event_type=type_map[event_type],
 function_name=function,
 payload=event_payload,
 context={}
 )

 # Process
 async def final_handler(evt: Event):
 return await dispatcher.dispatch(evt)

 result = await middleware.execute(event, final_handler)
 click.echo(f" Result: {json.dumps(result, indent=2)}")

 asyncio.run(run())

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), required=True,
 help='Path to configuration YAML file')
def validate(config: str):
 """Validate configuration file."""
 try:
 with open(config) as f:
 cfg = yaml.safe_load(f)

 # Validate required fields
 errors = []

 if 'services' not in cfg:
 errors.append("Missing 'services' section")
 else:
 for i, svc in enumerate(cfg['services']):
 required = ['name', 'namespace', 'service_name', 'port']
 for field in required:
 if field not in svc:
 errors.append(f"Service {i}: missing '{field}'")

 if errors:
 click.echo(" Configuration validation failed:")
 for error in errors:
 click.echo(f" - {error}")
 raise click.Abort()

 click.echo(" Configuration is valid")
 click.echo(f"\n Services configured: {len(cfg['services'])}")
 for svc in cfg['services']:
 click.echo(f" - {svc['name']} → {svc['namespace']}/{svc['service_name']}:{svc['port']}")

 except yaml.YAMLError as e:
 click.echo(f" Invalid YAML: {e}")
 raise click.Abort()

@cli.command()
@click.argument('output', type=click.Path())
def init(output: str):
 """Generate a sample configuration file."""
 sample_config = {
 'services': [
 {
 'name': 'my-function',
 'namespace': 'default',
 'service_name': 'my-service',
 'port': 8080,
 'path': '/invoke'
 }
 ],
 'middleware': {
 'logging': {
 'enabled': True,
 'level': 'INFO'
 },
 'validation': {
 'enabled': True
 }
 },
 'server': {
 'host': '0.0.0.0',
 'port': 8000,
 'timeout': 30
 }
 }

 output_path = Path(output)
 if output_path.exists():
 if not click.confirm(f'{output} already exists. Overwrite?'):
 return

 with open(output_path, 'w') as f:
 yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)

 click.echo(f" Created sample config at {output}")
 click.echo(f"\nNext steps:")
 click.echo(f" 1. Edit {output} to configure your services")
 click.echo(f" 2. Validate: k8s-shim validate -c {output}")
 click.echo(f" 3. Run: k8s-shim serve -c {output}")

@cli.command()
@click.option('--namespace', '-n', default='default', help='Kubernetes namespace')
def list_services(namespace: str):
 """List available Kubernetes services."""
 from kubernetes import client, config

 try:
 config.load_kube_config()
 v1 = client.CoreV1Api()

 click.echo(f" Services in namespace '{namespace}':\n")
 services = v1.list_namespaced_service(namespace)

 for svc in services.items:
 ports = ', '.join([f"{p.port}/{p.protocol}" for p in svc.spec.ports])
 click.echo(f" {svc.metadata.name}")
 click.echo(f" Type: {svc.spec.type}")
 click.echo(f" Ports: {ports}")
 click.echo()

 except Exception as e:
 click.echo(f" Error: {e}")
 raise click.Abort()

if __name__ == '__main__':
 cli()
