from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-poi-manager",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Django application for managing Points of Interest with geospatial capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-poi-manager",
    packages=find_packages(exclude=["poi_manager_project", "tests", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 5.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.11",
    install_requires=[
        "Django>=5.2,<5.3",
        "djangorestframework>=3.16",
        "django-filter>=25.0",
        "django-cors-headers>=4.7",
        "django-rq>=3.1",
        "rq>=2.5",
        "redis>=5.2",
        "psycopg[c,pool]>=3.2",
        "lxml>=5.3",
        "Pillow>=11.3",
    ],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "mypy",
            "pytest",
            "pytest-django",
            "pytest-cov",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="django poi geospatial gis postgis",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/django-poi-manager/issues",
        "Source": "https://github.com/yourusername/django-poi-manager",
        "Documentation": "https://github.com/yourusername/django-poi-manager/wiki",
    },
)