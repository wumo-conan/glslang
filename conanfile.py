from conans import ConanFile, CMake, tools
import os


class GLSLangConan(ConanFile):
    name = "glslang"
    version = "master-tot"
    url = "https://github.com/KhronosGroup/glslang"
    description = "Khronos reference front-end for GLSL and ESSL, and sample SPIR-V generator"
    settings = "os", "arch", "compiler", "build_type"
    
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    generators = "cmake"
    no_copy_source = True


    def source(self):
        tools.get(f"{self.url}/archive/{self.version}.tar.gz")

    def configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_SHARED_LIBS"]=self.options.shared
        cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"]=self.options.fPIC
        cmake.definitions["ENABLE_GLSLANG_BINARIES"] = True
        cmake.configure(source_dir=os.path.join(
            self.source_folder, f"glslang-{self.version}"))
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        cmake = self.configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info(
            'Appending PATH environment variable: {}'.format(bindir))
        self.env_info.PATH.append(bindir)
