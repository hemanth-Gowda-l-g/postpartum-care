import sys

try:
    from setuptools import setup  # type: ignore
    print("Using setuptools for setup.", file=sys.stderr)
except ImportError:
    try:
        from distutils.core import setup  # type: ignore
        print("Using distutils.core for setup.", file=sys.stderr)
    except ImportError:
        print("Error: setuptools and distutils.core not found. Please install setuptools.", file=sys.stderr)
        sys.exit(1)

setup(
    name="postpartum-care-platform",
    version="1.0.0",
    description="Postpartum Care Platform with Nutrition Prediction",
    author="Your Name",
    packages=['app'],
    include_package_data=True,
    install_requires=[
        'flask>=2.0.1',
        'flask-cors>=3.0.10',
        'flask-pymongo>=2.3.0',
        'flask-jwt-extended>=4.3.1',
        'python-dotenv>=0.19.0',
        'pymongo>=3.12.0',
        'scikit-learn>=1.0.2',
        'numpy>=1.21.2',
        'pandas>=1.3.3',
        'joblib>=1.1.0',
    ],
    python_requires='>=3.8,<3.12',
    setup_requires=['setuptools>=65.5.1', 'wheel>=0.38.0'],
) 