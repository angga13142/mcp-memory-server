#!/usr/bin/env python3
"""
Monitor load test execution and track metrics in real-time.
"""

import argparse
import time
from datetime import datetime

import requests


def monitor_load_test(duration_seconds=300, check_interval=5):
    """
    Monitor system during load test. 
    
    Args:
        duration_seconds: How long to monitor (default: 5 minutes)
        check_interval: How often to check (default: 5 seconds)
    """
    print(f"🔍 Monitoring Load Test")
    print(f"Duration: {duration_seconds}s")
    print(f"Check Interval: {check_interval}s")
    print("="*60)
    print(f"{'Time':<20} {'Status':<10} {'Response':<15} {'Memory':<15}")
    print("="*60)
    
    start_time = time.time()
    check_count = 0
    error_count = 0
    
    while time.time() - start_time < duration_seconds: 
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        try:
            # Check metrics endpoint (Using port 8081 as configured)
            start = time.time()
            response = requests.get("http://localhost:8081", timeout=5)
            response_time = (time.time() - start) * 1000
            
            # Check health endpoint
            # We use /sse for fastmcp running
            try:
                health = requests.get("http://localhost:8080/health", timeout=5)
                health_ok = health.status_code == 200
            except:
                # Try sse
                try:
                    health = requests.get("http://localhost:8080/sse", timeout=5)
                    health_ok = health.status_code == 200
                except:
                    health_ok = False
            
            if response.status_code == 200 and health_ok:
                status = "✅ OK"
            else:
                status = "⚠️  WARN"
                error_count += 1
            
            # Get memory usage from metrics
            memory_line = [line for line in response.text.split('\n') 
                          if 'mcp_system_memory_usage_bytes' in line and not line.startswith('#')]
            
            if memory_line: 
                memory_bytes = float(memory_line[0].split()[-1])
                memory_mb = memory_bytes / 1024 / 1024
                memory_str = f"{memory_mb:.1f} MB"
            else:
                memory_str = "N/A"
            
            response_str = f"{response_time:.1f} ms"
            
            print(f"{current_time:<20} {status:<10} {response_str:<15} {memory_str:<15}")
            
        except Exception as e:
            error_count += 1
            print(f"{current_time:<20} {'❌ ERROR':<10} {'N/A':<15} {'N/A':<15} {str(e)[:20]}")
        
        time.sleep(check_interval)
    
    # Summary
    print("="*60)
    print(f"Monitoring complete!")
    print(f"Total checks: {check_count}")
    print(f"Errors: {error_count}")
    if check_count > 0:
        print(f"Success rate: {((check_count - error_count) / check_count * 100):.2f}%")
    else:
        print("Success rate: 0.00%")
    print("="*60)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Monitor load test execution")
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    try:
        monitor_load_test(args.duration, args.interval)
    except KeyboardInterrupt: 
        print("\n\n⚠️  Monitoring interrupted by user")
