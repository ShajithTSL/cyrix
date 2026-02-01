from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="cyrix",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
)
