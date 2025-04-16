from setuptools import setup, find_packages

setup(
    name="llama_cpp_binaries",
    version="0.1.0",
    description="Binaries for llama.cpp server",
    packages=find_packages(),
    package_data={
        'llama_cpp_binaries': ['bin/*'],
    },
    include_package_data=True,
)
