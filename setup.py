# https://packaging.python.org/tutorials/distributing-packages/

from setuptools import setup, find_packages

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='flange',
    version='0.1.0',
    author='flashashen',
    author_email='flashashen@gmail.com',
    description='Autoload configuration from multiple sources, object registry, dpath access.',
    license = "MIT",
    url="https://github.com/flashashen/flange",
    classifiers= [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Environment :: Console',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 4 - Beta',

    ],
    platforms='osx,linux,mswindows',
    keywords="configuration yaml object registry spring",
    long_description=README_TEXT,
    packages=find_packages(exclude=['test']),
    py_modules=['flange'],
    install_requires=[
        'anyconfig',
        'PyYAML',
        'jsonschema',
        'dpath'
    ],
)