from setuptools import find_packages, setup  # type: ignore[import-untyped]

setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
)
