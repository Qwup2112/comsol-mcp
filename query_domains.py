#!/usr/bin/env python
"""
Query available domains and entities in geometry for proper selection.
This helps identify correct domain indices for material and coil assignment.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import mph

print("=" * 70)
print("DOMAIN QUERY DIAGNOSTIC")
print("=" * 70)

# Start COMSOL
print("\nStarting COMSOL...")
client = mph.start(cores=4, version="6.2")

# Create model
model = client.create("test_domain_model")
jm = model.java

# Create component
comp = jm.component().create('comp1', True)

# Create geometry
print("Creating geometry...")
geom = comp.geom().create('geom1', 2)

# Create rectangles (same as main script)
rect1 = geom.feature().create('rect1', 'Rectangle')
rect1.set('size', ['2', '10'])
rect1.set('pos', ['-6', '0'])

rect2 = geom.feature().create('rect2', 'Rectangle')
rect2.set('size', ['2', '10'])
rect2.set('pos', ['6', '0'])

rect3 = geom.feature().create('rect3', 'Rectangle')
rect3.set('size', ['14', '2'])
rect3.set('pos', ['-7', '-7'])

rect4 = geom.feature().create('rect4', 'Rectangle')
rect4.set('size', ['70', '70'])
rect4.set('pos', ['-35', '-35'])

# Create difference
dif1 = geom.feature().create('dif1', 'Difference')
dif1.selection('input').set(['rect4'])
dif1.selection('input2').set(['rect1', 'rect2', 'rect3'])

# Run geometry
geom.run()
print("✓ Geometry created")

# Query available domains
print("\nQuerying domains...")
try:
    # Method 1: Try to get all domain selections
    selections = geom.selection()
    print(f"Geometry selections available: {selections}")
    
    # Try to list domain tags
    print("\nAttempting to query domain information...")
    
    # Method 2: Check if we can get domain count
    try:
        # Try accessing the Java geom object directly
        java_geom = comp.geom('geom1')
        print(f"Java geom object: {java_geom}")
        
        # List available selections
        java_geom.selection('all').toString()
    except Exception as e:
        print(f"Error accessing Java geom: {e}")
    
    # Method 3: Try creating physics and check what domains it can see
    print("\nCreating physics to check domain visibility...")
    mf = comp.physics().create('mf', 'InductionCurrents', 'geom1')
    mf_node = mf.feature()
    
    # Try to create a coil and see what selection options exist
    coil_test = mf_node.create('coil_test', 'Coil')
    coil_selection = coil_test.selection()
    print(f"Coil selection object: {coil_selection}")
    
    # Try with different integer ranges
    print("\nTrying domain selections with different indices...")
    
    test_indices = [
        [0],      # 0-indexed
        [1],      # 1-indexed
        [0, 1],   # Multiple 0-indexed
        [1, 2],   # Multiple 1-indexed
        [0, 1, 2, 3],  # All 4 domains
    ]
    
    for indices in test_indices:
        try:
            coil_selection.set(indices)
            print(f"  ✓ Selection {indices} succeeded")
            break
        except Exception as e:
            print(f"  ✗ Selection {indices} failed: {str(e)[:80]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nCleaning up...")
client.close()
print("✓ Done")
