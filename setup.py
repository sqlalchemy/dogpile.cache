import os
import re
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


v = open(
    os.path.join(
        os.path.dirname(__file__),
        'dogpile', '__init__.py')
)
VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
v.close()

readme = os.path.join(os.path.dirname(__file__), 'README.rst')

setup(
    name='dogpile.cache',
    version=VERSION,
    description="A caching front-end based on the Dogpile lock.",
    long_description=open(readme).read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    keywords='caching',
    author='Mike Bayer',
    author_email='mike_mp@zzzcomputing.com',
    url='http://bitbucket.org/zzzeek/dogpile.cache',
    license='BSD',
    packages=find_packages('.', exclude=['tests*']),
    entry_points="""
    [mako.cache]
    dogpile.cache = dogpile.cache.plugins.mako_cache:MakoPlugin
    """,
    zip_safe=False,
    tests_require=['pytest', 'pytest-cov', 'mock', 'Mako'],
    cmdclass={'test': PyTest},
)
