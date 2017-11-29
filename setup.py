from setuptools import setup

setup(
    name='facerec',
    version='0.0.1dev',
    packages=['project'],
    license='Apache License 2.0',
    long_description=open('README.md').read(),
    install_requires=[dep.strip() for dep in open('requirements.txt')
                      if not dep.startswith('#') and
                      not dep.startswith('http://') and
                      not dep.startswith('https://')],
)

