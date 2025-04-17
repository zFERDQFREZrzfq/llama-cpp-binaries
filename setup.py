import glob
import os
import platform
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
        cmake_args = os.environ.get("CMAKE_ARGS", "").split()

        # Define directories
        llama_cpp_dir = os.path.abspath("llama.cpp")
        build_dir = os.path.abspath("build")
        bin_dir = os.path.join(build_dir, "bin")
        llama_dir = os.environ.get("LLAMA_CPP_BINARIES_DIR", "llama_cpp_binaries")
        target_dir = os.path.join(self.build_lib, llama_dir, "bin")

        # Create directories
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)

        # Platform-specific RPATH settings
        system = platform.system()
        if system == "Linux":
            cmake_args.extend([
                "-DCMAKE_INSTALL_RPATH=$ORIGIN",
                "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF"
            ])
        elif system == "Darwin":  # macOS
            cmake_args.extend([
                "-DCMAKE_INSTALL_RPATH=@executable_path",
                "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF"
            ])

        # Configure and build
        cmake_cmd = ["cmake", llama_cpp_dir] + cmake_args
        subprocess.check_call(cmake_cmd, cwd=build_dir)

        jobs = os.environ.get("LLAMA_CPP_BUILD_JOBS", "")
        build_cmd = ["cmake", "--build", ".", "--config", "Release", "-j" + jobs]
        subprocess.check_call(build_cmd, cwd=build_dir)

        # Handle Windows Release directory if present
        if os.path.exists(os.path.join(bin_dir, "Release")):
            bin_dir = os.path.join(bin_dir, "Release")

        # Copy binaries
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
