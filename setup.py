import glob
import os
import shutil
import subprocess

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name):
        # Don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])

class CMakeBuild(build_ext):
    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)

    def build_cmake(self, ext):
        # Get CMAKE_ARGS from environment
        cmake_args = os.environ.get("CMAKE_ARGS", "")

        # Create build directory
        build_dir = os.path.abspath("build")
        os.makedirs(build_dir, exist_ok=True)

        # Get submodule path
        llama_cpp_dir = os.path.abspath("llama.cpp")

        # Configure with CMake
        cmake_cmd = ["cmake", llama_cpp_dir] + cmake_args.split()
        subprocess.check_call(cmake_cmd, cwd=build_dir)

        # Build with multiple cores
        build_cmd = ["cmake", "--build", ".", "--config", "Release", "-j"]
        subprocess.check_call(build_cmd, cwd=build_dir)

        # Copy all files from bin directory to package
        bin_dir = os.path.join(build_dir, "bin")
        llama_dir = next((d for d in os.listdir(self.build_lib) if d.startswith("llama_cpp_binaries") and os.path.isdir(os.path.join(self.build_lib, d))), "llama_cpp_binaries")
        target_dir = os.path.join(self.build_lib, llama_dir, "bin")
        os.makedirs(target_dir, exist_ok=True)

        # Check for Windows-style Release subdirectory
        if os.path.exists(os.path.join(bin_dir, "Release")):
            bin_dir = os.path.join(bin_dir, "Release")

        for file in glob.glob(os.path.join(bin_dir, "*")):
            shutil.copy(file, target_dir)

setup(
    name="llama_cpp_binaries",
    version="0.1.0",
    description="Binaries for llama.cpp server",
    packages=find_packages(),
    ext_modules=[CMakeExtension("llama_cpp_binaries")],
    cmdclass={"build_ext": CMakeBuild},
    package_data={"llama_cpp_binaries": ["bin/*"]},
)
