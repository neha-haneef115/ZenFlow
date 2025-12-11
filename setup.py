from setuptools import setup, find_packages

setup(
    name="zenflow",  
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt5>=5.15.0"
    ],
    entry_points={
        "console_scripts": [
            "zenflowapp = main:main", 
        ],
    },
    include_package_data=True,
    author="Neha Haneef",
    description="ZenFlow - Focus & Productivity App",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/neha-haneef115/ZenFlow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
