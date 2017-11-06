# https://packaging.python.org/tutorials/distributing-packages/

from setuptools import setup

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='flange',
    version='0.0.2',
    author='flashashen',
    author_email='flashashen@gmail.com',
    description='Autoload configuration from multiple sources. Autotranslate config into usable object',
    license = "MIT",
    url="https://github.com/flashashen/flange",
    classifiers= [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
        'Environment :: Console',
        'Operating System :: Windows',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 3 - Alpha',

    ],
    platforms='osx,linux,mswindows',
    keywords = "configuration yaml object registry spring",
    long_description=README_TEXT,
    package_dir = {'': 'src'},
    packages=['util'],
    py_modules=['flange'],
    install_requires=[
        'anyconfig',
        'certifi',
        'chardet',
        'idna',
        'PyYAML',
        'requests',
        'six',
        # 'SQLAlchemy',
        'urllib3',
        'jsonschema'
    ],

    # entry_points='''
    #     [console_scripts]
    #     nyttth=no_you_talk_to_the_hand:cli
    # ''',
)