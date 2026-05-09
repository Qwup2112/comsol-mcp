"""Introspect the COMSOL Coil feature for InductionCurrents."""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
os.environ['COMSOL_ROOT'] = r'D:\COMSOL62'

import mph

print("Starting COMSOL...")
client = mph.start(cores=4, version='6.2')
model = client.create('coil_feature_probe')
jm = model.java
comp = jm.component().create('comp1', True)
geom = comp.geom().create('geom1', 2)
rect = geom.feature().create('r1', 'Rectangle')
rect.set('size', ['10', '10'])
rect.set('pos', ['0', '0'])
geom.run()

print('Creating physics...')
mf = comp.physics().create('mf', 'InductionCurrents', 'geom1')
print('Physics created:', mf)

print('Creating coil feature...')
coil = mf.feature().create('coil1', 'Coil')
print('Coil created:', coil)

names = [n for n in dir(coil) if not n.startswith('_')]
print('Methods/properties:', names)

for candidate in ['properties', 'get', 'set', 'help', 'tags', 'selection', 'label']:
    try:
        attr = getattr(coil, candidate)
        if callable(attr):
            try:
                result = attr()
            except TypeError:
                result = '<callable requires args>'
        else:
            result = attr
        print(f'{candidate}:', result)
    except Exception as e:
        print(f'{candidate}: ERROR {e}')

try:
    print('Help:', coil.help())
except Exception as e:
    print('help() failed:', e)

try:
    print('Tag:', coil.tag())
except Exception as e:
    print('tag() failed:', e)

try:
    print('Type/class:', coil.getClass())
except Exception as e:
    print('getClass() failed:', e)

client.clear()
print('Done')
