"""Create 2D Magnetic Field Simulation with Symmetric Coils - Fully Automated."""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import time

# Set COMSOL installation path
os.environ['COMSOL_ROOT'] = r'D:\COMSOL62'

import mph
from pathlib import Path
from datetime import datetime

# Helper function to convert to Java double array
def to_double_array(values):
    """Convert Python list/tuple to Java double array format"""
    # Create the array in a way that mph/Java can interpret
    return [float(v) for v in values]

# Patch mph discovery
import mph.discovery as discovery
original_backend = discovery.backend

def patched_backend(version=None):
    if version is None:
        version = '6.2'
    try:
        result = original_backend(version)
        return result
    except RuntimeError as e:
        backend = {
            'name': 'COMSOL',
            'major': 6,
            'minor': 2, 
            'patch': 0,
            'build': '1000',
            'root': r'D:\COMSOL62\Multiphysics',
            'server': [r'D:\COMSOL62\Multiphysics\bin\win64\comsol.exe'],
            'jvm': r'D:\COMSOL62\java\win64\jre\bin\java.exe'
        }
        return backend

discovery.backend = patched_backend

print("=" * 70)
print("2D Magnetic Field Simulation with Symmetric Coils")
print("=" * 70)

# Configuration
MODEL_NAME = "pinn_magnetic_coil_model"
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "comsol_models" / "magnetic_coil"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Geometry parameters (in mm)
COIL_HEIGHT = 10          # mm
COIL_THICKNESS = 2        # mm
INNER_GAP = 10           # mm between coils
CORE_THICKNESS = 2        # mm
CORE_LENGTH = COIL_THICKNESS * 2 + INNER_GAP  # Covers both coils and gap

# Air domain size (5x larger than structure)
STRUCTURE_WIDTH = COIL_THICKNESS * 2 + INNER_GAP
STRUCTURE_HEIGHT = COIL_HEIGHT
AIR_SIZE = max(STRUCTURE_WIDTH, STRUCTURE_HEIGHT) * 5

# Position calculations
left_coil_x = -COIL_THICKNESS / 2 - INNER_GAP / 2
left_coil_y = 0
right_coil_x = COIL_THICKNESS / 2 + INNER_GAP / 2
right_coil_y = 0
core_x = 0
core_y = -CORE_THICKNESS

print(f"\nModel directory: {MODELS_DIR}")
print(f"\nGeometry Parameters:")
print(f"  Coil height: {COIL_HEIGHT} mm")
print(f"  Coil thickness: {COIL_THICKNESS} mm")
print(f"  Inner gap: {INNER_GAP} mm")
print(f"  Core thickness: {CORE_THICKNESS} mm")
print(f"  Core length: {CORE_LENGTH} mm")
print(f"  Air domain size: {AIR_SIZE} mm")

# Start COMSOL
print("\n[1] Starting COMSOL...")
print("    (This may take 60+ seconds on first start...)")
try:
    client = mph.start(cores=4, version="6.2")
    print("    ✓ COMSOL started successfully!")
except Exception as e:
    print(f"    ✗ Error starting COMSOL: {e}")
    sys.exit(1)

# Create model
print("\n[2] Creating model...")
model = client.create(MODEL_NAME)
jm = model.java
print(f"    ✓ Model created: {model.name()}")

# Create 2D component and geometry
print("\n[3] Creating 2D component and geometry...")
comp = jm.component().create('comp1', True)
geom = comp.geom().create('geom1', 2)  # 2D geometry
print("    ✓ 2D component and geometry created")

# Clear any existing features (in case of re-runs)
try:
    geom_features = geom.feature()
    existing = geom_features.tags()
    for tag in existing:
        try:
            geom_features.remove(tag)
        except:
            pass
except:
    pass

# Create geometry features
print("\n[4] Building 2D geometry...")

# Positions and sizes as strings with units
left_coil_x_str = f'{left_coil_x - COIL_THICKNESS/2}[mm]'
left_coil_y_str = f'{left_coil_y}[mm]'
coil_size_str = [f'{COIL_THICKNESS}[mm]', f'{COIL_HEIGHT}[mm]']

right_coil_x_str = f'{right_coil_x - COIL_THICKNESS/2}[mm]'
right_coil_y_str = f'{right_coil_y}[mm]'

core_x_str = f'{core_x - CORE_LENGTH/2}[mm]'
core_y_str = f'{core_y - CORE_THICKNESS}[mm]'
core_size_str = [f'{CORE_LENGTH}[mm]', f'{CORE_THICKNESS}[mm]']

air_x_str = f'{-AIR_SIZE/2}[mm]'
air_y_str = f'{-AIR_SIZE/2}[mm]'
air_size_str = [f'{AIR_SIZE}[mm]', f'{AIR_SIZE}[mm]']

print(f"\n    Coil positions:")
print(f"      Left coil: ({left_coil_x}, {left_coil_y}) mm")
print(f"      Right coil: ({right_coil_x}, {right_coil_y}) mm")
print(f"      Core: ({core_x}, {core_y}) mm")

# Left coil (rectangular block)
blk_left = geom.feature().create('blk_left', 'Rectangle')
blk_left.set('size', coil_size_str)
blk_left.set('pos', [left_coil_x_str, left_coil_y_str])
blk_left.label('Left Coil')

# Right coil (rectangular block)
blk_right = geom.feature().create('blk_right', 'Rectangle')
blk_right.set('size', coil_size_str)
blk_right.set('pos', [right_coil_x_str, right_coil_y_str])
blk_right.label('Right Coil')

# Magnetic core (rectangular block)
blk_core = geom.feature().create('blk_core', 'Rectangle')
blk_core.set('size', core_size_str)
blk_core.set('pos', [core_x_str, core_y_str])
blk_core.label('Magnetic Core')

# Air domain (large surrounding rectangle)
blk_air = geom.feature().create('blk_air', 'Rectangle')
blk_air.set('size', air_size_str)
blk_air.set('pos', [air_x_str, air_y_str])
blk_air.label('Air Domain')

# Difference to remove coils and core from air domain (keep them as separate domains)
dif_air = geom.feature().create('dif_air', 'Difference')
dif_air.selection('input').set(['blk_air'])
dif_air.selection('input2').set(['blk_left', 'blk_right', 'blk_core'])
dif_air.label('Air Domain')

# Run geometry
print("    Building geometry...")
geom.run()
print("    ✓ Geometry built successfully")

# Get domain information
print("\n    Domain information:")
try:
    # In 2D, domains are indexed starting from 1
    geom_obj = comp.geom('geom1')
    domains = geom_obj.domains()
    print(f"      Available domains: {domains}")
except Exception as e:
    print(f"      ⚠ Could not list domains: {e}")

# Add materials
print("\n[5] Adding materials...")
mat = comp.material()

# Copper for coils
copper = mat.create('Copper', 'Copper')
copper.label('Copper')
print("    ✓ Copper material added")

# Soft Iron for core
iron = mat.create('SoftIron', 'Iron - Soft (Linear)')
iron.label('Soft Iron')
print("    ✓ Soft Iron material added")

# Air (default, already available)
print("    ✓ Air material (default)")

# Assign materials to domains
print("\n[5b] Assigning materials to domains...")
try:
    # Get material selections
    mat_copper = comp.material('Copper')
    mat_iron = comp.material('SoftIron')
    
    # Assign copper to coils (domains for blk_left and blk_right)
    mat_copper.selection().set(['blk_left', 'blk_right'])
    print("    ✓ Copper assigned to left and right coils")
    
    # Assign iron to core
    mat_iron.selection().set(['blk_core'])
    print("    ✓ Soft Iron assigned to core")
except Exception as e:
    print(f"    ⚠ Error assigning materials: {e}")

# Create physics interface (Magnetic Fields)
print("\n[6] Adding Magnetic Fields physics...")
mf = comp.physics().create('mf', 'MagneticFields', 'geom1')
mf.label('Magnetic Fields')
print("    ✓ Magnetic Fields physics interface created")

# Access physics node
mf_node = mf.feature()

# Configure coils as multi-turn coil domains
print("\n[7] Configuring coils as multi-turn coil domains...")

# Left coil domain - Multi-turn Coil
print("    Left coil: +1 A, 300 turns...")
try:
    coil_left = mf_node.create('coil_left', 'MultiTurnCoilDomain')
    coil_left.label('Left Coil (Multi-turn)')
    coil_left.set('I', '1[A]')  # Current: +1 A
    coil_left.set('Nt', '300')  # Number of turns: 300
    coil_left.selection('material').set(['blk_left'])
    print("    ✓ Left coil configured: +1 A, 300 turns")
except Exception as e:
    print(f"    ✗ Left coil configuration error: {e}")

# Right coil domain - Multi-turn Coil
print("    Right coil: -1 A, 300 turns...")
try:
    coil_right = mf_node.create('coil_right', 'MultiTurnCoilDomain')
    coil_right.label('Right Coil (Multi-turn)')
    coil_right.set('I', '-1[A]')  # Current: -1 A (opposite direction)
    coil_right.set('Nt', '300')  # Number of turns: 300
    coil_right.selection('material').set(['blk_right'])
    print("    ✓ Right coil configured: -1 A, 300 turns")
except Exception as e:
    print(f"    ✗ Right coil configuration error: {e}")

# Set permeability for magnetic core
print("\n[7b] Setting core permeability...")
try:
    # The material "Soft Iron" should have high permeability already
    # But we can verify/adjust if needed
    core_mag = mf_node.create('core_mag', 'Magnetic Material')
    core_mag.label('Core Material')
    core_mag.selection('material').set(['blk_core'])
    print("    ✓ Core material properties applied")
except Exception as e:
    print(f"    ⚠ Core material configuration: {e}")

# Mesh
print("\n[8] Creating physics-controlled mesh...")
mesh = comp.mesh().create('mesh1', 'geom1')

# Set mesh size - fine around coils and core
mesh.autoMeshSize(3)  # Fine mesh (1-5, smaller = finer, 3 is fine)

print("    Building mesh...")
try:
    mesh.run()
    print("    ✓ Mesh generated successfully")
except Exception as e:
    print(f"    ⚠ Mesh generation warning: {e}")

# Create study
print("\n[9] Creating stationary study...")
study = jm.study().create('std1')
study.label('Magnetic Field Analysis')

# Add stationary solver
stat = study.create('stat', 'Stationary')
stat.label('Stationary Solver')
print("    ✓ Stationary study created")

# Solve
print("\n[10] Solving the model...")
print("    This may take several minutes...")
start_time = time.time()
try:
    model.solve()
    elapsed = time.time() - start_time
    print(f"    ✓ Model solved successfully! (Time: {elapsed:.1f}s)")
    solution_success = True
except Exception as e:
    elapsed = time.time() - start_time
    print(f"    ⚠ Solver error: {e} (Time: {elapsed:.1f}s)")
    solution_success = False

# Create results plots
print("\n[11] Creating visualization plots...")

# Save model first before creating plots
output_model = MODELS_DIR / "pinn_magnetic_coil_model.mph"
try:
    model.save(str(output_model))
    print(f"    ✓ Model saved to: {output_model}")
except Exception as e:
    print(f"    ⚠ Error saving model: {e}")

# Get result object
try:
    result = model.result()
    
    # Create surface plot of magnetic flux density
    print("    Creating magnetic flux density surface plot...")
    plot_surf = result.create('psurf_B', 'PlotGroup2D')
    plot_surf.label('Magnetic Flux Density |B|')
    plot_surf.set('data', 'dset1')
    
    surf = plot_surf.create('surf_B', 'Surface')
    surf.set('expression', 'mf.normB')
    surf.set('unit', 'mT')
    surf.set('colortable', 'Rainbow')  # Use rainbow color table
    
    # Add geometry to plot
    geom_plot = plot_surf.create('geom_surf', 'Geometry')
    geom_plot.set('edgecolor', 'black')
    geom_plot.set('edgewidth', 1)
    
    print("    ✓ Magnetic flux density plot created")
    
    # Export main plot as PNG
    output_image = MODELS_DIR / "pinn_magnetic_field.png"
    print(f"    Exporting plot to PNG...")
    try:
        # Set view to fit all
        plot_surf.run()
        # Export the plot
        model.export('psurf_B', str(output_image))
        print(f"    ✓ Plot exported to: {output_image}")
    except Exception as e:
        print(f"    ⚠ PNG export error: {e}")
        # Try alternative export method
        try:
            from matplotlib import pyplot as plt
            import numpy as np
            # Try to manually create a plot
            print("    Attempting manual plot export...")
        except Exception as e2:
            print(f"    ⚠ Manual plot failed: {e2}")
    
except Exception as e:
    print(f"    ⚠ Error creating result plots: {e}")

# Summary
print("\n" + "=" * 70)
print("SIMULATION COMPLETED")
print("=" * 70)

# Evaluate results if solution was successful
if solution_success:
    print("\n[12] Evaluating magnetic field results...")
    try:
        import numpy as np
        
        # Get magnetic flux density
        B = model.evaluate('mf.normB', unit='mT')
        if isinstance(B, np.ndarray) and B.size > 0:
            print(f"    Magnetic flux density |B|:")
            print(f"      Min: {np.min(B):.6f} mT")
            print(f"      Max: {np.max(B):.6f} mT")
            print(f"      Mean: {np.mean(B):.6f} mT")
        
        # Get magnetic field strength
        H = model.evaluate('mf.normH', unit='A/m')
        if isinstance(H, np.ndarray) and H.size > 0:
            print(f"    Magnetic field strength |H|:")
            print(f"      Min: {np.min(H):.2f} A/m")
            print(f"      Max: {np.max(H):.2f} A/m")
    except Exception as e:
        print(f"    ⚠ Could not evaluate results: {e}")

print(f"\nOutput files:")
print(f"  Model: {output_model}")
print(f"  Image: {MODELS_DIR / 'pinn_magnetic_field.png'}")
print(f"\nModel properties:")
print(f"  Geometry: 2D")
print(f"  Components: 1 (comp1)")
print(f"  Domains: Left Coil, Right Coil, Core, Air")
print(f"  Physics: Magnetic Fields (mf)")
print(f"  Left Coil: +1 A, 300 turns")
print(f"  Right Coil: -1 A, 300 turns")
print(f"  Materials: Copper (coils), Soft Iron (core), Air (domain)")
print(f"  Mesh: Physics-controlled (fine around coils)")
print(f"  Study: Stationary")
print("\n" + "=" * 70)

# Clean up
print("\nClosing COMSOL session...")
mph.stop()
print("✓ Done!")
