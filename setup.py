import glob
import os
import platform
import shutil
import subprocess

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

# Skip building if env var is set
skip_build = os.environ.get("SKIP_EXTENSION_BUILD", "0") == "1"

# Package name from env or default
package_name = os.environ.get("LLAMA_CPP_BINARIES_DIR", "llama_cpp_binaries")


class CMakeExtension(Extension):
    def __init__(self, name):
        # Just a placeholder extension that doesn't need sources
        super().__init__(name, sources=[])


class CMakeBuild(build_ext):
    def run(self):
        if skip_build:
            print("Skipping extension build as requested by SKIP_EXTENSION_BUILD=1")
            return

        for ext in self.extensions:
            self.build_cmake(ext)

    def build_cmake(self, ext):
        cmake_args = os.environ.get("CMAKE_ARGS", "").split()

        llama_cpp_dir = os.path.abspath("llama.cpp")
        build_dir = os.path.abspath("build")
        package_dir = os.path.join(self.build_lib, package_name)

        # Get variants to build (default, cuda, etc.)
        variants = os.environ.get("LLAMA_CPP_VARIANTS", "default").split(",")

        for variant in variants:
            variant = variant.strip()
            print(f"Building variant: {variant}")

            # Fresh build each time
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
            os.makedirs(build_dir, exist_ok=True)

            # Setup variant-specific paths
            if variant == "cuda":
                target_dir = os.path.join(package_dir, "bin", "cuda")
                lib_rel_path = "../../lib"
            elif variant == "tensorcores":
                target_dir = os.path.join(package_dir, "bin", "cuda-tensorcores")
                lib_rel_path = "../../lib"
            else:
                target_dir = os.path.join(package_dir, "bin")
                lib_rel_path = "../lib"

            os.makedirs(target_dir, exist_ok=True)

            # Set RPATH differently based on platform
            system = platform.system()
            if system == "Linux":
                cmake_args.extend([
                    f"-DCMAKE_INSTALL_RPATH=$ORIGIN:$ORIGIN/{lib_rel_path}",
                    "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                    "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF"
                ])
            elif system == "Darwin":
                cmake_args.extend([
                    f"-DCMAKE_INSTALL_RPATH=@executable_path:@executable_path/{lib_rel_path}",
                    "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                    "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF"
                ])

            # Build it
            cmake_cmd = ["cmake", llama_cpp_dir] + cmake_args
            subprocess.check_call(cmake_cmd, cwd=build_dir)

            jobs = os.environ.get("LLAMA_CPP_BUILD_JOBS", "")
            build_cmd = ["cmake", "--build", ".", "--config", "Release"]
            build_cmd.append(f"-j{jobs}")

            subprocess.check_call(build_cmd, cwd=build_dir)

            # Handle Windows-style paths if needed
            bin_dir = os.path.join(build_dir, "bin")
            if os.path.exists(os.path.join(bin_dir, "Release")):
                bin_dir = os.path.join(bin_dir, "Release")

            # Copy everything to target dir
            for file in glob.glob(os.path.join(bin_dir, "*")):
                shutil.copy(file, target_dir)


setup(
    name=package_name,
    version="0.1.0",
    description="Binaries for llama.cpp server",
    packages=find_packages(),
    ext_modules=[CMakeExtension(package_name)],
    cmdclass={"build_ext": CMakeBuild},
    package_data={package_name: ["bin/*", "bin/cuda/*", "bin/cuda-tensorcores/*", "lib/*", "**/*.py"]},
)
