import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

version_file = (here / 'src/rad_arduino_proxy/_version.py').read_text(encoding='utf-8')
version = None

for line in version_file.splitlines():
    if line.startswith('__version__'):
        delim = '"' if '"' in line else "'"
        version = line.split(delim)[1]
        break
else:
    raise RuntimeError('Unable to find version string.')

setup(
    name='rad_arduino_proxy',
    version=version,
    author='Ryan Dellana',
    author_email='rdellan@sandia.gov',
    url='https://github.com/rdellan/rad-arduino-proxy',
    license='BSD',
    license_files=['LICENSE'],
    description='Python Library for Lightweight Packet Serial Communication with Multiple Arduinos',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Education'
    ],
    keywords='arduino',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6',
    install_requires=['pyserial >= 3.4.0', 'cobs >= 1.2.0']
)
