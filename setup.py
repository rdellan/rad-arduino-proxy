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


    python_requires='>=3.7',
    install_requires=['requests ~= 2.28.0'],
    extras_require={
        'dev': [
            'autopep8 ~= 1.6.0',
            'flake8 ~= 4.0.1',
            'flake8-commas ~= 2.1.0',
            'flake8-docstrings ~= 1.6.0',
            'flake8-isort ~= 4.1.1',
            'flake8-quotes ~= 3.3.1',
            'isort ~= 5.10.1',
            'mypy ~= 0.961',
            'pep8-naming ~= 0.13.0',
            'pytest ~= 7.1.2',
            'sphinx <= 4.3',  # pinned to <= 4.3, because 4.4 requires importlib_metadata >= 4.4, which is not compatible with flake8 >= 4
            'sphinx-autodoc-typehints <= 1.17',  # pinned to <= 1.17, because 1.18 requires Sphinx >= 4.5, which is not compatible with flake8 >= 4
            'sphinx-markdown-builder == 0.5.4',  # pinned to 0.5.4, because 0.5.5 has a formatting bug
            'types-requests ~= 2.28.0',
        ],
    },
)
