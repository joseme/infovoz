from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="asistente-voz",
    version="1.0.0",
    author="Tu Nombre",
    author_email="tu@email.com",
    description="Asistente de voz con múltiples APIs y TTS de calidad",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tuusuario/asistente-voz",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "premium": [
            "google-cloud-texttospeech>=2.14.0",
            "openai>=1.0.0",
        ],
        "web": [
            "gunicorn>=20.0.0",
            "uvicorn>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "asistente-voz=asistente_voz.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "asistente_voz": [
            "models/*",
            "assets/*",
            "config/*.json",
        ],
    },
)