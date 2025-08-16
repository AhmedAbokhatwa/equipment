from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in equipment/__init__.py
from equipment import __version__ as version

setup(
	name="equipment",
	version=version,
	description="Equipment",
	author="Equipment",
	author_email="Equipment@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
