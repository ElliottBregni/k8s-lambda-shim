"""Tests for service registry."""
import pytest

from shim.registry.service_registry import ServiceRegistry, ServiceEndpoint


class TestServiceEndpoint:
    def test_generates_url_correctly(self):
        endpoint = ServiceEndpoint(
            namespace="prod",
            service_name="my-service",
            port=8080,
            path="/api/v1"
        )
        expected = "http://my-service.prod.svc.cluster.local:8080/api/v1"
        assert endpoint.url == expected
    
    def test_uses_default_values(self):
        endpoint = ServiceEndpoint(service_name="test-service")
        assert endpoint.namespace == "default"
        assert endpoint.port == 80
        assert endpoint.path == "/"
        assert endpoint.url == "http://test-service.default.svc.cluster.local:80/"


class TestServiceRegistry:
    def test_register_and_lookup(self):
        registry = ServiceRegistry()
        endpoint = ServiceEndpoint(service_name="test-service")
        
        registry.register("test-function", endpoint)
        result = registry.lookup("test-function")
        
        assert result == endpoint
    
    def test_lookup_returns_none_for_unknown_function(self):
        registry = ServiceRegistry()
        result = registry.lookup("unknown-function")
        assert result is None
    
    def test_load_from_config(self):
        config = {
            "func1": {
                "service_name": "service1",
                "namespace": "ns1",
                "port": 9000
            },
            "func2": {
                "service_name": "service2"
            }
        }
        
        registry = ServiceRegistry()
        registry.load_from_config(config)
        
        endpoint1 = registry.lookup("func1")
        assert endpoint1.service_name == "service1"
        assert endpoint1.namespace == "ns1"
        assert endpoint1.port == 9000
        
        endpoint2 = registry.lookup("func2")
        assert endpoint2.service_name == "service2"
        assert endpoint2.namespace == "default"
