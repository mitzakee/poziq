from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="poziq",
    version="0.1.0",
    author="Radu Coanda",
    author_email="me@coanda.xyz",
    description="A tool for slicing, encoding, and assembling images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mitzakee/poziq",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=["click == 8.1.7", "Pillow==11.0.0"],
    extras_require={
        "dev": [
            "pytest==8.3.4",
            "pytest-cov==6.0.0",
            "black",
            "isort",
        ],
    },
    entry_points={
        "console_scripts": [
            "poziq=poziq.cli:cli",
        ],
    },
)
