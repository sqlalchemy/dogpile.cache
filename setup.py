import os
import sys
import re

from setuptools import setup, find_packages

v = open(os.path.join(os.path.dirname(__file__), 'dogpile', 'cache', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
v.close()

readme = os.path.join(os.path.dirname(__file__), 'README.rst')

setup(name='dogpile.cache',
      version=VERSION,
      description="A caching front-end based on the Dogpile lock.",
      long_description=open(readme).read(),
      classifiers=[
      'Development Status :: 3 - Alpha',
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
      packages=find_packages('.', exclude=['ez_setup', 'tests*']),
      namespace_packages=['dogpile'],
      entry_points="""
      [mako.cache]
      dogpile = dogpile.cache.plugins.mako:MakoPlugin
      """,
      zip_safe=False,
      install_requires=['dogpile.core>=0.3.0'],
      test_suite='nose.collector',
      tests_require=['nose'],
)
