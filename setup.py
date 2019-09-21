import os
import re
import sys

from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand


class UseTox(TestCommand):
    RED = 31
    RESET_SEQ = "\033[0m"
    BOLD_SEQ = "\033[1m"
    COLOR_SEQ = "\033[1;%dm"

    def run_tests(self):
        sys.stderr.write(
            "%s%spython setup.py test is deprecated by pypa.  Please invoke "
            "'tox' with no arguments for a basic test run.\n%s"
            % (self.COLOR_SEQ % self.RED, self.BOLD_SEQ, self.RESET_SEQ)
        )
        sys.exit(1)


v = open(os.path.join(os.path.dirname(__file__), "dogpile", "__init__.py"))
VERSION = (
    re.compile(r""".*__version__ = ["'](.*?)["']""", re.S)
    .match(v.read())
    .group(1)
)
v.close()

readme = os.path.join(os.path.dirname(__file__), "README.rst")

setup(
    name="dogpile.cache",
    version=VERSION,
    description="A caching front-end based on the Dogpile lock.",
    long_description=open(readme).read(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    keywords="caching",
    author="Mike Bayer",
    author_email="mike_mp@zzzcomputing.com",
    url="https://github.com/sqlalchemy/dogpile.cache",
    license="BSD",
    packages=find_packages(".", exclude=["tests*"]),
    entry_points="""
    [mako.cache]
    dogpile.cache = dogpile.cache.plugins.mako_cache:MakoPlugin
    """,
    zip_safe=False,
    install_requires=["decorator>=4.0.0"],
    cmdclass={"test": UseTox},
)
