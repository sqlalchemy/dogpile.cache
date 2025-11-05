"""Nox configuration for dogpile.cache."""

from __future__ import annotations

import glob
import itertools
import os
import sys

import nox

nox.needs_version = ">=2025.10.16"


if True:
    sys.path.insert(0, ".")
    from tools.toxnox import tox_parameters
    from tools.toxnox import apply_pytest_opts


PYTHON_VERSIONS = [
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.13t",
    "3.14",
    "3.14t",
]
TARGETS = [
    "generic",
    "memory",
    "memcached",
    "redis",
    "redis_sentinel",
    "valkey",
    "valkey_sentinel",
    "dbm",
]
FULL = ["_quick", "full"]

pyproject = nox.project.load_toml("pyproject.toml")

nox.options.sessions = ["simple"]
nox.options.tags = ["py-generic-memory-dbm"]


def _pifpaf(
    cmd: list[str],
    module: str,
    *,
    port_env: str = "TOX_DOGPILE_PORT",
    port: str = "11234",
    additonal_args: str = "",
) -> None:
    """prepend a pifpaf execution to the given command arguments.

    This runs a server like memcached or redis up front before invoking
    the subsequent commands.

    """
    cmd[:0] = (
        f"pifpaf --env-prefix DOGPILE run {module} --port "
        f"{os.environ.get(port_env, port)} {additonal_args} --".split()
    )


@nox.session(name="simple")
@tox_parameters(
    ["python", "target", "full"],
    [PYTHON_VERSIONS, ["generic-memory-dbm"], FULL],
    always_include_in_tag=["target"],
)
def test_simple(session: nox.Session, target: str, full: str) -> None:
    """run a general suite including two built-in backends"""
    _tests(session, ["generic", "memory", "dbm"], full=full == "full")


@nox.session(name="backends")
@tox_parameters(
    ["python", "target", "full"],
    [PYTHON_VERSIONS, TARGETS, FULL],
)
def test_backends(session: nox.Session, target: str, full: str) -> None:
    """Run the main test suite, with optional single backend tests"""

    _tests(session, [target], full=full == "full")


@nox.session(name="coverage")
@tox_parameters(["target"], [TARGETS], base_tag="coverage")
def coverage(session: nox.Session, target: str) -> None:
    """Run tests with coverage."""

    _tests(session, [target], coverage=True)


def _tests(
    session: nox.Session,
    targets: list[str],
    coverage: bool = False,
    full: bool = False,
) -> None:

    if coverage:
        session.install("-e", ".")
    else:
        session.install(".")

    session.install(*nox.project.dependency_groups(pyproject, "tests"))

    if coverage:
        session.install(*nox.project.dependency_groups(pyproject, "coverage"))

    cmd = ["python", "-m", "pytest"]

    if coverage:
        cmd.extend(
            [
                "--cov=dogpile",
                "--cov-append",
                "--cov-report",
                "term",
                "--cov-report",
                "xml",
            ]
        )

        # run "full" for generic which squeezes out a few more lines
        # of coverage for lock.py
        if "generic" in targets:
            full = True

    if not full:
        # disable time_intensive
        cmd.extend(["-m", "not time_intensive"])

    backend_cmd: list[str] = []
    pifpaf_cmd: list[str] = []

    ports = itertools.count(11212)

    for target in targets:
        # note the default target is "generic", which means run all the
        # normal tests but no backend tests

        match target:
            case "generic":
                backend_cmd.extend(
                    [
                        path
                        for path in glob.glob("tests/**/*.py", recursive=True)
                        if "backend" not in path
                    ]
                )
                backend_cmd.append("tests/cache/test_null_backend.py")
            case "memory":
                backend_cmd.append("tests/cache/test_memory_backend.py")
            case "memcached":
                session.install(
                    *nox.project.dependency_groups(
                        pyproject,
                        "tests_memcached",
                    )
                )

                if full:
                    # special install of pylibmc from source for full build
                    # this can't be in pyproject.toml since it's rejected
                    # by pypi
                    session.install(
                        "pylibmc @ "
                        "git+https://github.com/lericson/pylibmc.git@master"
                    )

                _pifpaf(
                    pifpaf_cmd,
                    "memcached",
                    port=str(next(ports)),
                )
                _pifpaf(
                    pifpaf_cmd,
                    "memcached",
                    port_env="TOX_DOGPILE_TLS_PORT",
                    port=str(next(ports)),
                    additonal_args=(
                        "--ssl_chain_cert=tests/tls/server_chain.pem "
                        "--ssl_key=tests/tls/server.key"
                    ),
                )

                backend_cmd.append("tests/cache/test_memcached_backend.py")
            case "redis":
                session.install(
                    *nox.project.dependency_groups(pyproject, "tests_redis")
                )
                _pifpaf(pifpaf_cmd, "redis", port=str(next(ports)))
                backend_cmd.append("tests/cache/test_redis_backend.py")
            case "valkey":
                session.install(
                    *nox.project.dependency_groups(pyproject, "tests_valkey")
                )
                _pifpaf(pifpaf_cmd, "valkey", port=str(next(ports)))
                backend_cmd.append("tests/cache/test_valkey_backend.py")
            case "redis_sentinel":
                session.install(
                    *nox.project.dependency_groups(pyproject, "tests_redis")
                )

                _pifpaf(
                    pifpaf_cmd,
                    "redis",
                    port=str(next(ports)),
                    additonal_args=f"--sentinel  --sentinel "
                    f"--sentinel-port "
                    f"""{os.environ.get(
                        'TOX_DOGPILE_SENTINEL_PORT', str(next(ports)))}""",
                )
                backend_cmd.append(
                    "tests/cache/test_redis_sentinel_backend.py"
                )
            case "valkey_sentinel":
                session.install(
                    *nox.project.dependency_groups(pyproject, "tests_valkey")
                )
                _pifpaf(
                    pifpaf_cmd,
                    "valkey",
                    port=str(next(ports)),
                    additonal_args=f"--sentinel  --sentinel "
                    f"--sentinel-port "
                    f"""{os.environ.get(
                        'TOX_DOGPILE_SENTINEL_PORT', str(next(ports)))}""",
                )
                backend_cmd.append(
                    "tests/cache/test_valkey_sentinel_backend.py"
                )
            case "dbm":
                backend_cmd.append("tests/cache/test_dbm_backend.py")

    posargs = apply_pytest_opts(
        session,
        "dogpile",
        targets,
        coverage=coverage,
    )

    session.run(*pifpaf_cmd, *cmd, *backend_cmd, *posargs)


@nox.session(name="pep484")
def mypy_check(session: nox.Session) -> None:
    """Run mypy type checking."""

    session.install(*nox.project.dependency_groups(pyproject, "mypy"))

    session.install("-e", ".")

    session.run("mypy", "noxfile.py", "./dogpile/")


@nox.session(name="pep8")
def lint(session: nox.Session) -> None:
    """Run linting and formatting checks."""

    session.install(*nox.project.dependency_groups(pyproject, "lint"))

    file_paths = [
        "./dogpile/",
        "./tests/",
        "./tools/",
        "noxfile.py",
        "docs/build/conf.py",
    ]
    session.run("flake8", *file_paths)
    session.run("black", "--check", *file_paths)
