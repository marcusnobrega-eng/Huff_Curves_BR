from setuptools import find_packages, setup


setup(
    name="huff-curves-br",
    version="0.1.0",
    description="Download ANA sub-daily rainfall data and derive empirical Huff curves for Brazilian stations.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "dataclasses>=0.8; python_version < '3.7'",
        "numpy>=1.19,<1.20; python_version < '3.7'",
        "numpy>=1.21,<1.22; python_version == '3.7'",
        "numpy>=1.24; python_version >= '3.8'",
        "pandas>=1.1,<1.2; python_version < '3.7'",
        "pandas>=1.3,<1.4; python_version == '3.7'",
        "pandas>=2.0; python_version >= '3.8'",
        "requests>=2.27,<2.28; python_version < '3.7'",
        "requests>=2.27,<3; python_version >= '3.7'",
        "matplotlib>=3.3,<3.4; python_version < '3.7'",
        "matplotlib>=3.5,<3.6; python_version == '3.7'",
        "matplotlib>=3.7; python_version >= '3.8'",
    ],
    extras_require={
        "geo": [
            "geopandas>=0.9,<0.10; python_version < '3.7'",
            "geopandas>=0.10,<0.11; python_version == '3.7'",
            "geopandas>=0.14; python_version >= '3.8'",
            "shapely>=1.7,<2; python_version < '3.8'",
            "shapely>=2.0; python_version >= '3.8'",
            "fiona>=1.8,<1.9; python_version < '3.8'",
            "pyogrio>=0.7; python_version >= '3.8'",
        ],
        "dev": [
            "pytest>=6,<7; python_version < '3.7'",
            "pytest>=7,<8; python_version == '3.7'",
            "pytest>=8.0; python_version >= '3.8'",
        ],
    },
)
