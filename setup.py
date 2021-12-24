# https://packaging.python.org/tutorials/distributing-packages/

from setuptools import setup, find_packages

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='flange',
    version='1.0.1',
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
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development',
        'Environment :: Console',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 5 - Production/Stable',
    ],
    platforms='osx,linux,mswindows',
    keywords="configuration yaml object registry spring",
    long_description=README_TEXT,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=['test']),
    py_modules=['flange'],
    install_requires=[
        'anyconfig>=0.9.0',
        'PyYAML>=5.4',
        'jsonschema>=3.*',
        'dpath>=1.4.0'
    ],
)