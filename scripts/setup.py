#!/usr/bin/env python3
import os
import re

from setuptools import find_packages, setup


#Read the package version from __init__.py
def get_version():
    with open(os.path.join("app", "__init__.py"), encoding="utf-8") as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
        if version_match:
            return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


#Read the package description from README.md
def get_long_description():
    with open("README.md", encoding="utf-8") as f:
        return f.read()


#Read requirements from requirements.txt
def get_requirements():
    with open("requirements.txt", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name="second-certainty",
    version=get_version(),
    author="Cesaire Tobias",
    author_email="cesaire@example.com",  #Replace with your actual email
    description="A South African tax liability management tool",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/ces0491/second-certainty",
    packages=find_packages(exclude=["tests*", "docs*"]),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=get_requirements(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    entry_points={
        "console_scripts": [
            "second-certainty=app.main:run_app",
            "sct-update-taxes=scripts.update_tax_tables:main",
            "sct-seed-data=scripts.seed_data:main",
        ],
    },
    #Add package data
    package_data={
        "app": ["templates/*.html", "static/**/*"],
    },
    zip_safe=False,
)
