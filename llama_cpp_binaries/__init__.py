__version__ = "0.1.0"

import os
import platform

import llama_cpp_binaries  # Import the package itself


def get_binary_path(variant=None):
    """Return the path to the appropriate llama-server binary"""
    system = platform.system()
    if system == "Windows":
        executable = "llama-server.exe"
    else:
        executable = "llama-server"

    # Get the package directory
    package_dir = os.path.dirname(os.path.abspath(llama_cpp_binaries.__file__))

    # Set bin directory based on variant
    if variant == 'cuda':
        bin_dir = os.path.join(package_dir, "bin", "cuda")
    elif variant == 'tensorcores':
        bin_dir = os.path.join(package_dir, "bin", "cuda-tensorcores")
    else:
        bin_dir = os.path.join(package_dir, "bin")

    return os.path.join(bin_dir, executable)
