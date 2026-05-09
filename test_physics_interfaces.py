"""Test script to discover available physics interfaces in COMSOL 6.2."""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
os.environ['COMSOL_ROOT'] = r'D:\COMSOL62'

import mph

print("=" * 70)
print("Physics Interface Discovery for COMSOL 6.2")
print("=" * 70)

# Start COMSOL
print("\n[1] Starting COMSOL...")
try:
    client = mph.start(cores=4, version="6.2")
    print("    ✓ COMSOL started")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

# Create a simple test model
print("\n[2] Creating test model...")
model = client.create("test_physics_discovery")
jm = model.java

# Create component and 2D geometry
print("\n[3] Creating 2D component and geometry...")
comp = jm.component().create('comp1', True)
geom = comp.geom().create('geom1', 2)

# Create a simple rectangle
rect1 = geom.feature().create('rect1', 'Rectangle')
rect1.set('size', ['10', '10'])
rect1.set('pos', ['0', '0'])
geom.run()
print("    ✓ Geometry created")

# Try to discover physics interfaces using Java reflection
print("\n[4] Attempting to discover physics interfaces...")
try:
    # Get the physics node directly
    physics_obj = comp.physics()
    print(f"    Physics object type: {type(physics_obj)}")
    print(f"    Physics object dir: {[x for x in dir(physics_obj) if not x.startswith('_')]}")
    
    # Try to get list of available physics
    try:
        # Try method: tags()
        tags = physics_obj.tags()
        print(f"    Available physics tags: {tags}")
    except Exception as e:
        print(f"    ✗ tags() failed: {e}")
    
    # Try different physics interface identifiers
    test_identifiers = [
        'mf', 'MagneticFields', 'Magnetic Fields',
        'Magnetostatics', 'MagnetoStatics', 'magnetostatics',
        'acdc', 'ACDC', 'AC/DC',
        'emqi', 'EMQI',  # Maybe it's embedded in another module
        'emQS',  # Electromagnetoquasistatics
    ]
        # Also test working identifier to validate discovery
        test_identifiers.extend([
            'LaminarFlow',  # Known to work
            'StationaryMagneticField',
            'ConductiveMedia',
            'ElectricCurrents',
            'Electrostatics',
            'es',  # Electrostatics short
            'ec',  # Electric Currents short
        ])
    
    print("\n[5] Testing physics interface identifiers...")
    for identifier in test_identifiers:
        try:
            test_physics = comp.physics().create('test', identifier, 'geom1')
            print(f"    ✓ SUCCESS: '{identifier}' created physics interface!")
            # Clean up
            comp.physics().remove('test')
            break
        except Exception as e:
            error_msg = str(e)
            if 'Unknown physics interface' in error_msg:
                print(f"    ✗ '{identifier}' - Unknown physics interface")
            else:
                print(f"    ? '{identifier}' - Other error: {type(e).__name__}")
    
except Exception as e:
    print(f"    ✗ Error during discovery: {e}")
    import traceback
    traceback.print_exc()

# Try opening an existing model to see what physics it has
print("\n[6] Checking existing models for physics interfaces...")
import glob
mph_files = glob.glob(r"d:\Download\COMSOL_Multiphysics_MCP\comsol_models\micromixer_fixed\*.mph")
if mph_files:
    try:
        existing_model = client.open(mph_files[0])
        print(f"    Opened: {mph_files[0]}")
        
        # Get components and their physics
        jm_existing = existing_model.java
        comps_list = jm_existing.component().tags()
        print(f"    Components: {comps_list}")
        
        if comps_list:
            comp_existing = jm_existing.component(comps_list[0])
            physics_list = comp_existing.physics().tags()
            print(f"    Physics in {comps_list[0]}: {physics_list}")
            
            # Get details of the first physics
            if physics_list:
                first_physics = physics_list[0]
                print(f"    First physics details: {comp_existing.physics(first_physics)}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

# Try listing models in the client
print("\n[6b] Checking client models...")
try:
    models = client.models()
    print(f"    Models in session: {models}")
    for m in models:
        print(f"    - {m.name()}")
except Exception as e:
    print(f"    ✗ Error listing models: {e}")
print("\n[7] Cleanup...")
client.clear()
print("    ✓ Done")
