import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pypetkit",
    version="0.0.4",
    author="Ben Horan",
    author_email="benh@geeksforhire.com.au",
    description="PetKit python integration library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geeks4hire/pypetkit",
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
