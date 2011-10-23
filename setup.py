import os
import sys

from setuptools import setup, find_packages

extra = {}
if sys.version_info >= (3, 0):
    extra.update(
        use_2to3=True,
    )

readme = os.path.join(os.path.dirname(__file__), 'README.rst')

setup(name='dogpile.cache',
      version="0.1.0",
      description="A caching front-end based on the Dogpile lock.",
      long_description=file(readme).read(),
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
      packages=find_packages(exclude=['ez_setup', 'tests']),
      namespace_packages=['dogpile'],
      entry_points="""
      [mako.cache]
      dogpile = dogpile.cache.plugins.mako_plugin:MakoPlugin
      """
      zip_safe=False,
      install_requires=['dogpile>=0.1.0'],
      test_suite='nose.collector',
      tests_require=['nose'],
      **extra
)
