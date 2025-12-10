"""
Live Quiz Socket.IO Server Package

This package implements a real-time quiz system similar to Kahoot,
using python-socketio AsyncServer for WebSocket communication.
"""

from .server import sio, socket_app

__all__ = ["sio", "socket_app"]
