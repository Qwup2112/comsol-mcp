"""Create 2D Axisymmetric Magnetic Field model for a single coil."""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
import time
from pathlib import Path

# Set COMSOL installation path
os.environ["COMSOL_ROOT"] = r"D:\COMSOL62"

import mph

# Patch mph discovery to ensure COMSOL 6.2 is found
import mph.discovery as discovery
original_backend = discovery.backend


def patched_backend(version=None):
    if version is None:
        version = "6.2"
    try:
        return original_backend(version)
    except RuntimeError:
        return {
            "name": "COMSOL",
            "major": 6,
            "minor": 2,
            "patch": 0,
            "build": "1000",
            "root": r"D:\COMSOL62\Multiphysics",
            "server": [r"D:\COMSOL62\Multiphysics\bin\win64\comsol.exe"],
            "jvm": r"D:\COMSOL62\java\win64\jre\bin\java.exe",
        }


discovery.backend = patched_backend

print("=" * 70)
print("2D Axisymmetric Magnetic Coil Simulation")
print("=" * 70)

# Configuration
MODEL_NAME = "axisymmetric_magnetic_coil"
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "comsol_models" / "magnetic_coil"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Geometry parameters (mm)
R_IN = 5.0
THICK = 2.0
HEIGHT = 10.0
AIR_RADIUS = 30.0

# Derived sizes (mm)
COIL_POS_R = R_IN
COIL_POS_Z = -HEIGHT / 2.0
COIL_SIZE = [f"{THICK}[mm]", f"{HEIGHT}[mm]"]
AIR_SIZE = [f"{AIR_RADIUS}[mm]", f"{2 * AIR_RADIUS}[mm]"]
AIR_POS = ["0[mm]", f"{-AIR_RADIUS}[mm]"]

print(f"\nOutput directory: {MODELS_DIR}")
print("\nGeometry Parameters:")
print(f"  Inner radius: {R_IN} mm")
print(f"  Thickness: {THICK} mm")
print(f"  Height: {HEIGHT} mm")
print(f"  Air radius: {AIR_RADIUS} mm")

# Start COMSOL
print("\n[1] Starting COMSOL...")
try:
    client = mph.start(cores=4, version="6.2")
    print("    ✓ COMSOL started successfully")
except Exception as e:
    print(f"    ✗ Error starting COMSOL: {e}")
    sys.exit(1)

# Create model
print("\n[2] Creating model...")
try:
    try:
        client.remove(MODEL_NAME)
    except Exception:
        pass
    model = client.create(MODEL_NAME)
    jm = model.java
    print(f"    ✓ Model created: {model.name()}")
except Exception as e:
    print(f"    ✗ Error creating model: {e}")
    sys.exit(1)

# Create component and axisymmetric geometry
print("\n[3] Creating 2D axisymmetric component and geometry...")
comp = jm.component().create("comp1", True)
geom = comp.geom().create("geom1", 2)
try:
    geom.axisymmetric(True)
    print("    ✓ Axisymmetric geometry enabled")
except Exception as e:
    print(f"    ⚠ Axisymmetric flag not set: {e}")

# Build geometry
print("\n[4] Building geometry...")
coil_rect = geom.feature().create("coil", "Rectangle")
coil_rect.set("size", COIL_SIZE)
coil_rect.set("pos", [f"{COIL_POS_R}[mm]", f"{COIL_POS_Z}[mm]"])
coil_rect.label("Coil")

air_rect = geom.feature().create("air", "Rectangle")
air_rect.set("size", AIR_SIZE)
air_rect.set("pos", AIR_POS)
air_rect.label("Air Domain")

air_diff = geom.feature().create("air_diff", "Difference")
air_diff.selection("input").set(["air"])
air_diff.selection("input2").set(["coil"])
try:
    air_diff.set("keep", True)
except Exception:
    pass

air_diff.label("Air Domain (Subtract Coil)")

print("    Running geometry...")
geom.run()
print("    ✓ Geometry created")

# Parameters for environment
print("\n[5] Setting environment parameters...")
try:
    jm.param().set("T_amb", "293.15[K]")
    jm.param().set("p_amb", "1[atm]")
    print("    ✓ Parameters set: T_amb, p_amb")
except Exception as e:
    print(f"    ⚠ Parameter set warning: {e}")

# Materials
print("\n[6] Adding materials...")
mat = comp.material()

try:
    mat_air = mat.create("mat_air", "Common")
    mat_air.label("Air")
    mat_air.propertyGroup("def").set("relpermeability", "1")
    mat_air.propertyGroup("def").set("electricconductivity", "0[S/m]")
    mat_air.propertyGroup("def").set("relpermittivity", "1")
    mat_air.selection().set(["air_diff"])
    print("    ✓ Air material assigned")
except Exception as e:
    print(f"    ⚠ Air material warning: {e}")

try:
    mat_copper = mat.create("mat_copper", "Common")
    mat_copper.label("Copper")
    mat_copper.propertyGroup("def").set("relpermeability", "1")
    mat_copper.propertyGroup("def").set("electricconductivity", "5.8e7[S/m]")
    mat_copper.selection().set(["coil"])
    print("    ✓ Copper material assigned")
except Exception as e:
    print(f"    ⚠ Copper material warning: {e}")

# Physics: Magnetic Fields (mf)
print("\n[7] Adding Magnetic Fields physics...")
try:
    mf = comp.physics().create("mf", "InductionCurrents", "geom1")
    mf.label("Magnetic Fields")
    print("    ✓ Magnetic Fields interface created")
except Exception as e:
    print(f"    ✗ Physics error: {e}")
    sys.exit(1)

print("\n[8] Configuring coil feature...")
try:
    mf_node = mf.feature()
    coil = mf_node.create("coil1", "Coil")
    coil.label("Coil (Homogenized Multi-turn)")
    coil.set("ICoil", "1[A]")
    coil.set("N", "200")
    coil.selection().set([1])
    print("    ✓ Coil configured: 1 A, 200 turns")
except Exception as e:
    print(f"    ⚠ Coil configuration warning: {e}")

# Mesh
print("\n[9] Creating physics-controlled mesh...")
mesh = comp.mesh().create("mesh1", "geom1")
mesh.autoMeshSize(2)  # Extra fine
try:
    mesh.run()
    print("    ✓ Mesh generated")
except Exception as e:
    print(f"    ⚠ Mesh warning: {e}")

# Study
print("\n[10] Creating stationary study...")
study = jm.study().create("std1")
study.create("stat", "Stationary")
print("    ✓ Stationary study created")

# Solve
print("\n[11] Solving...")
start_time = time.time()
try:
    model.solve()
    elapsed = time.time() - start_time
    print(f"    ✓ Solved successfully ({elapsed:.1f}s)")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"    ⚠ Solver warning: {e} ({elapsed:.1f}s)")

# Results
print("\n[12] Creating plots...")
result = model.result()

# B-field arrows
try:
    pg_B = result.create("pg_B", "PlotGroup2D")
    pg_B.label("Magnetic Flux Density (B)")
    pg_B.set("data", "dset1")

    arr = pg_B.create("arr1", "ArrowSurface")
    try:
        arr.set("expr", ["mf.Br", "mf.Bz"])
    except Exception:
        arr.set("expr", "mf.B")

    pg_B.run()
    output_B = MODELS_DIR / "axisymmetric_B_arrows.png"
    model.export("pg_B", str(output_B))
    print(f"    ✓ B-field arrows exported: {output_B}")
except Exception as e:
    print(f"    ⚠ B-field plot warning: {e}")

# Magnetic vector potential surface
try:
    pg_A = result.create("pg_A", "PlotGroup2D")
    pg_A.label("Magnetic Vector Potential")
    pg_A.set("data", "dset1")

    surf = pg_A.create("surf1", "Surface")
    surf.set("colortable", "Rainbow")

    try:
        surf.set("expr", "mf.Az")
    except Exception:
        surf.set("expr", "mf.Aphi")

    pg_A.run()
    output_A = MODELS_DIR / "axisymmetric_A_potential.png"
    model.export("pg_A", str(output_A))
    print(f"    ✓ Vector potential exported: {output_A}")
except Exception as e:
    print(f"    ⚠ Vector potential plot warning: {e}")

# Save model
print("\n[13] Saving model...")
output_model = MODELS_DIR / "axisymmetric_magnetic_coil.mph"
try:
    model.save(str(output_model))
    print(f"    ✓ Model saved: {output_model}")
except Exception as e:
    print(f"    ⚠ Save warning: {e}")

print("\nDone.")

# Clean up
try:
    mph.stop()
except Exception:
    pass
