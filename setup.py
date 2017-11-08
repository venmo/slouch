import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requires = [
    'docopt-unicode == 0.6.1',  # https://github.com/docopt/docopt/pull/220
    'mock',
    'requests',
    'slacker >= 0.5.1',
    'websocket-client',
]

with open('README.rst') as f:
    readme = f.read()

# This hack is from http://stackoverflow.com/a/7071358/1231454;
# the version is kept in a seperate file and gets parsed - this
# way, setup.py doesn't have to import the package.

VERSIONFILE = 'slouch/_version.py'

version_line = open(VERSIONFILE).read()
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)

setup(
    name='slouch',
    version=version,
    description='A lightweight framework for building cli-inspired Slack bots.',
    long_description=readme,
    author='Simon Weber',
    author_email='simon@venmo.com',
    url='https://github.com/venmo/slouch',
    packages=['slouch'],
    include_package_data=True,
    install_requires=requires,
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)
