import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pygumroad",
    version="0.0.3",
    author="Brennon Thomas",
    author_email="info@opsdisk.com",
    description="A Python API client for interacting with the Gumroad API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opsdisk/pygumroad",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests>=2.24.0",
        "requests-toolbelt>=0.9.1",
        "appengine-python-standard>=1.1.4"
    ],
    python_requires=">=3.6",
    license="GNU General Public License v3.0",
    keywords="python gumroad api client",
)
