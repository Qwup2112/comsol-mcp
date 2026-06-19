# comsol-mcp

Utilities and experiments for driving COMSOL through Python (`mph`).

## Install COMSOL for this project

This repository does not include COMSOL itself. You must install it locally with a valid license.

### 1) Confirm target setup

- OS: Linux / macOS / Windows
- COMSOL version: `6.2` is the default expected by current scripts
- License mode: local file or floating network license

### 2) Install COMSOL from licensed media

1. Download installer media from your COMSOL account.
2. Run the COMSOL installer with administrator/root privileges.
3. Install the modules and LiveLink components you need for your workflows.

### 3) Configure environment variables

Set these before running scripts in this repository:

- `COMSOL_ROOT`: COMSOL install root (for example `D:\COMSOL62` on Windows)
- `COMSOL_MULTIPHYSICS_ROOT` (optional): defaults to `<COMSOL_ROOT>/Multiphysics`
- `COMSOL_EXECUTABLE` (optional): full path to `comsol` executable
- `COMSOL_VERSION` (optional): defaults to `6.2`
- `COMSOL_CORES` (optional): defaults to `1`
- `LMCOMSOL_LICENSE_FILE` or `LM_LICENSE_FILE`: license file or license server (for example `1718@license-server`)

### 4) Install Python package dependency

```bash
python -m pip install mph
```

### 5) Verify COMSOL detection

Run repository verification script:

```bash
python verify_comsol_install.py
```

To also test starting COMSOL through `mph`:

```bash
python verify_comsol_install.py --check-mph-start
```

## Notes

- COMSOL binaries and license assets are proprietary and are not vendored in this repository.
- In CI or container setups, install COMSOL outside source control and provide the environment variables above.