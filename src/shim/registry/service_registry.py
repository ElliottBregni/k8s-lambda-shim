"""K8s service registry for Lambda function name to service endpoint mapping."""
from typing import Optional
from pydantic import BaseModel

class ServiceEndpoint(BaseModel):
 namespace: str = "default"
 service_name: str
 port: int = 80
 path: str = "/"

 @property
 def url(self) -> str:
 return f"http://{self.service_name}.{self.namespace}.svc.cluster.local:{self.port}{self.path}"

class ServiceRegistry:
 def __init__(self):
 self._mappings: dict[str, ServiceEndpoint] = {}

 def register(self, function_name: str, endpoint: ServiceEndpoint):
 self._mappings[function_name] = endpoint

 def lookup(self, function_name: str) -> Optional[ServiceEndpoint]:
 return self._mappings.get(function_name)

 def load_from_config(self, config: dict[str, dict]):
 for func_name, endpoint_config in config.items():
 self.register(
 func_name,
 ServiceEndpoint(**endpoint_config)
 )
