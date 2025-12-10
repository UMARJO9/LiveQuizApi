"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

This configuration combines Django ASGI application with Socket.IO
for real-time quiz functionality.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

import django
from django.core.asgi import get_asgi_application

# Setup Django BEFORE importing socket server
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Import socket server after Django setup
from sockets.server import sio


# Create combined ASGI application
async def application(scope, receive, send):
    """
    Combined ASGI application that routes requests to either
    Django or Socket.IO based on the path.

    Socket.IO requests go to /socket.io/
    All other requests go to Django
    """
    if scope["type"] == "http":
        path = scope.get("path", "")
        if path.startswith("/socket.io"):
            await sio.handle_request(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    elif scope["type"] == "websocket":
        await sio.handle_request(scope, receive, send)
    else:
        await django_asgi_app(scope, receive, send)
