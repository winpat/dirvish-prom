import setuptools

setuptools.setup(
    name="dirvish-prom",
    version="1.0.0",
    author="Patrick Winter",
    author_email="patrickwinter@posteo.ch",
    description="Prometheus exporter for dirvish",
    python_requires=">=3.8",
    py_modules=["dirvish_prom"],
    entry_points={"console_scripts": ["dirvish-prom=dirvish_prom:main"]},
)
