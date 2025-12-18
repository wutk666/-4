import sys
import traceback

try:
    print("Testing imports...")
    from app import create_app
    print("✓ create_app imported")
    
    app = create_app()
    print("✓ App created")
    
    # Check routes
    attack_routes = [str(rule) for rule in app.url_map.iter_rules() if 'attack' in str(rule)]
    print(f"\n✓ Found {len(attack_routes)} attack routes:")
    for route in attack_routes:
        print(f"  - {route}")
    
    print("\n✓ All imports successful!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
