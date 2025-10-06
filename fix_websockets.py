"""
Temporary fix for websockets.asyncio import issue
"""
import sys

# Create a comprehensive fake asyncio module
class FakeAsyncIOClient:
    def __init__(self, *args, **kwargs):
        # Accept any arguments but don't do anything
        self._args = args
        self._kwargs = kwargs

    def __getattr__(self, name):
        # Return a dummy method that accepts any arguments
        return lambda *args, **kwargs: None

class FakeRealtimeClient:
    def __init__(self, *args, **kwargs):
        # Accept any arguments for realtime clients
        self._args = args
        self._kwargs = kwargs
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class FakeAsyncIOModule:
    class client:
        ClientConnection = FakeAsyncIOClient

# Patch websockets
import websockets
if not hasattr(websockets, 'asyncio'):
    websockets.asyncio = FakeAsyncIOModule()

# Set in sys.modules for subprocess imports
sys.modules['websockets.asyncio'] = FakeAsyncIOModule()
sys.modules['websockets.asyncio.client'] = FakeAsyncIOModule.client

# Patch realtime imports by pre-creating the module
realtime_async_client = type(sys)('realtime._async.client')
realtime_async_client.ClientConnection = FakeAsyncIOClient
realtime_async_client.AsyncRealtimeClient = FakeRealtimeClient
sys.modules['realtime._async.client'] = realtime_async_client

# Also patch the main realtime module
realtime_module = type(sys)('realtime')
realtime_module.AuthorizationError = Exception
realtime_module.NotConnectedError = Exception
realtime_module.AsyncRealtimeChannel = FakeRealtimeClient
realtime_module.AsyncRealtimeClient = FakeRealtimeClient
realtime_module.SyncRealtimeChannel = FakeRealtimeClient
realtime_module.SyncRealtimeClient = FakeRealtimeClient
realtime_module.RealtimeChannelOptions = type('RealtimeChannelOptions', (), {})
sys.modules['realtime'] = realtime_module

print("✅ Applied websockets.asyncio monkey patch")
