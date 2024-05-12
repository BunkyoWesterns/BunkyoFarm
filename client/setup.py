import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="exploitfarm",
    version="{{VERSION_PLACEHOLDER}}",
    author="Pwnzer0tt1",
    author_email="pwnzer0tt1@poliba.it",
    scripts=["xfarm"],
    install_requires=[
        "typer==0.12.3",
        "PyInquirer==1.0.3",
        "requests==2.31.0"
    ],
    description="Exploit Farm client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pwnzer0tt1/exploitfarm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
