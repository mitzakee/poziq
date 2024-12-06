from setuptools import setup, find_packages

setup(
    name="poziq",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click>=8.0.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "poziq=poziq.cli:cli",
        ],
    },
)
