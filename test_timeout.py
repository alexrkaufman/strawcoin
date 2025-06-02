#!/usr/bin/env python3

import os
import sys
sys.path.append('.')

from src import create_app
from src.config import DevelopmentConfig, ProductionConfig

def test_timeout_config():
    """Test session timeout configuration in different modes."""
    
    print("🔍 Testing Session Timeout Configuration")
    print("=" * 50)
    
    # Test 1: Default app creation
    print("\n1. Default app creation:")
    app1 = create_app()
    print(f"   Debug: {app1.debug}")
    print(f"   Timeout: {app1.config.get('SESSION_TIMEOUT_SECONDS')} seconds")
    print(f"   Config class: {app1.config.__class__.__name__}")
    
    # Test 2: Force development config
    print("\n2. Forced development config:")
    app2 = create_app()
    app2.config.from_object(DevelopmentConfig)
    print(f"   Debug: {app2.debug}")
    print(f"   Timeout: {app2.config.get('SESSION_TIMEOUT_SECONDS')} seconds")
    print(f"   Config class: {app2.config.__class__.__name__}")
    
    # Test 3: Force production config
    print("\n3. Forced production config:")
    app3 = create_app()
    app3.config.from_object(ProductionConfig)
    print(f"   Debug: {app3.debug}")
    print(f"   Timeout: {app3.config.get('SESSION_TIMEOUT_SECONDS')} seconds")
    print(f"   Config class: {app3.config.__class__.__name__}")
    
    # Test 4: Check config classes directly
    print("\n4. Config classes directly:")
    dev_config = DevelopmentConfig()
    prod_config = ProductionConfig()
    print(f"   DevelopmentConfig timeout: {dev_config.SESSION_TIMEOUT_SECONDS} seconds")
    print(f"   ProductionConfig timeout: {prod_config.SESSION_TIMEOUT_SECONDS} seconds")
    
    print("\n" + "=" * 50)
    print("✅ Test complete - check timeout values above")

if __name__ == "__main__":
    test_timeout_config()