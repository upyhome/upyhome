from setuptools import setup, find_packages

setup(
    name='upyhome',
    version='0.1.0',
    author='upyHome',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'tabulate',
        'pyserial',
        'rshell',
        'esptool',
        'stringcase',
        'ruamel.yaml'

    ],
    entry_points={
        'console_scripts': [
            'upyhome=upyhome.__main__:cli'
        ]
        
    }
)