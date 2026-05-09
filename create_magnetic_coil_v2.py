"""Create 2D Magnetic Field Simulation with Symmetric Coils - Simplified Approach."""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import time

# Set COMSOL installation path
os.environ['COMSOL_ROOT'] = r'D:\COMSOL62'

import mph
from pathlib import Path

print("=" * 70)
print("2D Magnetic Field Simulation - SIMPLIFIED VERSION")
print("=" * 70)

# Configuration
MODEL_NAME = "pinn_magnetic_coil_model"
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "comsol_models" / "magnetic_coil"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print(f"\nOutput directory: {MODELS_DIR}")

# Start COMSOL
print("\n[1] Starting COMSOL...")
try:
    client = mph.start(cores=4, version="6.2")
    print("    ✓ COMSOL started successfully!")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

# Create and configure model
print("\n[2] Creating model...")
try:
    # Remove old model if exists
    try:
        client.remove(MODEL_NAME)
    except:
        pass
    
    model = client.create(MODEL_NAME)
    print(f"    ✓ Model created: {model.name()}")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

# Get Java model object
jm = model.java

# Create component
print("\n[3] Creating 2D component...")
try:
    comp = jm.component().create('comp1', True)
    print("    ✓ Component created")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

# Create 2D geometry
print("\n[4] Creating 2D geometry...")
try:
    geom = comp.geom().create('geom1', 2)
    
    # Add rectangles for coils and core
    # Left coil: centered at x=-6, y=0, size 2x10
    rect1 = geom.feature().create('rect1', 'Rectangle')
    rect1.set('size', ['2', '10'])  # Size must be positive
    rect1.set('pos', ['-7', '-5'])  # Position places the rectangle corner
    rect1.label('Left Coil')
    
    # Right coil: centered at x=6, y=0, size 2x10
    rect2 = geom.feature().create('rect2', 'Rectangle')
    rect2.set('size', ['2', '10'])  # Size positive
    rect2.set('pos', ['5', '-5'])   # Positioned from corner at x=5
    rect2.label('Right Coil')
    
    # Core below coils
    rect3 = geom.feature().create('rect3', 'Rectangle')
    rect3.set('size', ['14', '2'])  # 14mm (covers both coils and gap) x 2mm
    rect3.set('pos', ['-7', '-7'])  # Centered below coils
    rect3.label('Magnetic Core')
    
    # Large air domain
    rect4 = geom.feature().create('rect4', 'Rectangle')
    rect4.set('size', ['70', '70'])  # 70mm x 70mm
    rect4.set('pos', ['-35', '-35'])  # Centered
    rect4.label('Air Domain')
    
    # Create difference: air minus coils and core
    dif1 = geom.feature().create('dif1', 'Difference')
    dif1.selection('input').set(['rect4'])
    dif1.selection('input2').set(['rect1', 'rect2', 'rect3'])
    dif1.label('Air')
    
    # Run geometry
    geom.run()
    print("    ✓ Geometry created")
    print("      - Left coil: 2mm x 10mm at (-6, 0)")
    print("      - Right coil: 2mm x 10mm at (6, 0)")
    print("      - Core: 14mm x 2mm centered below")
    print("      - Air domain: 70mm x 70mm")
    
except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Add materials
print("\n[5] Adding materials...")
try:
    mat = comp.material()
    
    # Copper - left coil (domain 0)
    copper_l = mat.create('mat_copper_l', 'Common')
    copper_l.label('Copper Left')
    copper_l.propertyGroup('def').set('relpermeability', '1')
    copper_l.propertyGroup('def').set('electricconductivity', '5.8e7[S/m]')
    copper_l.selection().set([0])
    
    # Copper - right coil (domain 1)
    copper_r = mat.create('mat_copper_r', 'Common')
    copper_r.label('Copper Right')
    copper_r.propertyGroup('def').set('relpermeability', '1')
    copper_r.propertyGroup('def').set('electricconductivity', '5.8e7[S/m]')
    copper_r.selection().set([1])
    
    # Soft Iron - core (domain 2)
    iron = mat.create('mat_iron', 'Common')
    iron.label('Soft Iron')
    iron.propertyGroup('def').set('relpermeability', '1000')
    iron.selection().set([2])
    
    print("    ✓ Materials assigned")
    print("      - Copper: Left and Right Coils")
    print("      - Soft Iron: Magnetic Core")    
except Exception as e:
    print(f"    ⚠ Material warning: {e}")

# Add Magnetic Fields physics
print("\n[6] Adding Magnetic Fields physics...")
try:
    # Use MagneticFieldsCurrentsOnly from mph tags.json
    mf = comp.physics().create('mf', 'InductionCurrents', 'geom1')
    mf.label('Magnetic Fields')
    print("    ✓ Physics interface created")
    
except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Configure coils
print("\n[7] Configuring multi-turn coils...")
try:
    mf_node = mf.feature()
    
    # Left coil: +1 A, 300 turns
    coil_left = mf_node.create('coil_l', 'Coil')
    coil_left.set('ICoil', '1[A]')
    coil_left.set('N', '300')
    coil_left.selection().set([0])  # Domain 0: left coil
    coil_left.label('Left Coil Domain')
    
    # Right coil: -1 A, 300 turns  
    coil_right = mf_node.create('coil_r', 'Coil')
    coil_right.set('ICoil', '-1[A]')
    coil_right.set('N', '300')
    coil_right.selection().set([1])  # Domain 1: right coil
    coil_right.label('Right Coil Domain')
    
    print("    ✓ Coils configured")
    print("      - Left coil: +1 A, 300 turns")
    print("      - Right coil: -1 A, 300 turns")
    
except Exception as e:
    print(f"    ⚠ Coil warning: {e}")
    import traceback
    traceback.print_exc()

# Create mesh
print("\n[8] Creating mesh...")
try:
    mesh = comp.mesh().create('mesh1', 'geom1')
    mesh.autoMeshSize(3)  # Fine mesh
    mesh.run()
    print("    ✓ Mesh generated")
    
except Exception as e:
    print(f"    ⚠ Mesh warning: {e}")

# Create study
print("\n[9] Creating stationary study...")
try:
    study = jm.study().create('std1')
    study.create('stat', 'Stationary')
    print("    ✓ Study created")
    
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

# Solve
print("\n[10] Solving...")
print("    (This may take several minutes...)")
try:
    model.solve()
    print("    ✓ Solved successfully!")
    
except Exception as e:
    print(f"    ⚠ Solver warning: {e}")

# Create and export plot
print("\n[11] Creating result plot...")
try:
    result = jm.result()
    plot_surf = result.create('psurf_B', 'PlotGroup2D')
    plot_surf.label('Magnetic Flux Density |B|')
    plot_surf.set('data', 'dset1')

    # Create surface plot
    surf = plot_surf.create('surf_B', 'Surface')
    surf.set('colortable', 'Rainbow')

    plot_surf.run()
    output_image = MODELS_DIR / 'pinn_magnetic_field.png'
    model.export('psurf_B', str(output_image))
    print(f"    ✓ Plot exported to: {output_image}")
except Exception as e:
    print(f"    ⚠ Plot/export warning: {e}")

# Save model
print("\n[12] Saving model...")
try:
    output_model = MODELS_DIR / "pinn_magnetic_coil_model.mph"
    model.save(str(output_model))
    print(f"    ✓ Saved: {output_model}")
    
except Exception as e:
    print(f"    ✗ Error: {e}")

# Summary
print("\n" + "=" * 70)
print("SIMULATION COMPLETE")
print("=" * 70)
print(f"\nModel saved to:")
print(f"  {MODELS_DIR / 'pinn_magnetic_coil_model.mph'}")
print(f"\nConfiguration:")
print(f"  Geometry: 2D")
print(f"  Physics: Magnetic Fields (mf)")
print(f"  Left Coil: +1 A, 300 turns")
print(f"  Right Coil: -1 A, 300 turns")
print(f"  Study: Stationary")
print("\nYou can now open the model in COMSOL to:")
print("  - Create visualizations")
print("  - Export plots as images")
print("  - Evaluate magnetic field values")
print("\n" + "=" * 70)

# Cleanup
print("\nClosing COMSOL...")
try:
    # Don't clear - just end gracefully
    pass
except Exception:
    pass
print("✓ Done!")
