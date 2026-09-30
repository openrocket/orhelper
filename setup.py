import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="orhelper",
    version="0.1.6",
    author="Andrei Popescu and others",
    description="OrHelper is a module which aims to facilitate interacting and scripting with OpenRocket from Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openroket/orhelper",
    packages=setuptools.find_packages(),
    install_requires=[
        "jpype1>=0.6.3",
        "numpy"
    ],
    python_requires='>=3.6',
    include_package_data=True,
    package_data={
        'orhelper' : ['examples/*.py'],
    },
)
