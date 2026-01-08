#!/usr/bin/env python
"""Health check script for Docker container."""

import sys
from http.client import HTTPConnection

def check_health():
    """Check if server is responding."""
    try:
        conn = HTTPConnection("localhost", 8080, timeout=5)
        conn.request("GET", "/health")
        response = conn.getresponse()
        conn.close()
        
        if response.status == 200:
            return 0
        else:
            print(f"Health check failed with status {response.status}")
            return 1
    except Exception as e:
        print(f"Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
