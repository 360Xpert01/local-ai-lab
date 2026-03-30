from setuptools import setup, find_packages

setup(
    name="lab",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "httpx>=0.25.0",
        "watchdog>=3.0.0",
        "jinja2>=3.1.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "websockets>=12.0",
        "python-multipart>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "lab=lab.cli:main",
        ],
    },
    python_requires=">=3.11",
)
