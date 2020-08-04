import os

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration

class GLSLangConan(ConanFile):
    name = "glslang"
    version = "2020.2"
    url = "https://github.com/KhronosGroup/glslang"
    description = "Khronos reference front-end for GLSL and ESSL, and sample SPIR-V generator"
    exports_sources = ["CMakeLists.txt", "conanize.patch"]
    settings = "os", "arch", "compiler", "build_type"
    
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_executables": [True, False],
        "spv_remapper": [True, False],
        "hlsl": [True, False],
        "enable_optimizer": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_executables": True,
        "spv_remapper": True,
        "hlsl": True,
        "enable_optimizer": True
    }
    
    generators = "cmake"
    
    _cmake = None
    
    @property
    def _source_subfolder(self):
        return "source_subfolder"
    
    @property
    def _build_subfolder(self):
        return "build_subfolder"
    
    def requirements(self):
        if self.options.enable_optimizer:
            self.requires("spirv-tools/v2020.3")
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, 11)
        if self.options.shared and self.settings.os in ["Windows", "Macos"]:
            raise ConanInvalidConfiguration("Current glslang shared library build is broken on Windows and Macos")
    
    def source(self):
        revision = "3ee5f2f1d3316e228916788b300d786bb574d337"
        # tools.get(f"{self.url}/archive/{self.version}.tar.gz")
        tools.get(f"{self.url}/archive/{revision}.tar.gz")
        os.rename(self.name + "-" + revision, self._source_subfolder)
    
    def configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["BUILD_EXTERNAL"] = False
        self._cmake.definitions["SKIP_GLSLANG_INSTALL"] = False
        self._cmake.definitions["ENABLE_SPVREMAPPER"] = self.options.spv_remapper
        self._cmake.definitions["ENABLE_GLSLANG_BINARIES"] = self.options.build_executables
        self._cmake.definitions["ENABLE_GLSLANG_JS"] = False
        self._cmake.definitions["ENABLE_GLSLANG_WEBMIN"] = False
        self._cmake.definitions["ENABLE_GLSLANG_WEBMIN_DEVEL"] = False
        self._cmake.definitions["ENABLE_EMSCRIPTEN_SINGLE_FILE"] = False
        self._cmake.definitions["ENABLE_EMSCRIPTEN_ENVIRONMENT_NODE"] = False
        self._cmake.definitions["ENABLE_HLSL"] = self.options.hlsl
        self._cmake.definitions["ENABLE_RTTI"] = False
        self._cmake.definitions["ENABLE_OPT"] = self.options.enable_optimizer
        self._cmake.definitions["ENABLE_PCH"] = True
        self._cmake.definitions["ENABLE_CTEST"] = False
        self._cmake.definitions["USE_CCACHE"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake
    
    def build(self):
        tools.patch(base_path=self._source_subfolder, patch_file="conanize.patch")
        cmake = self.configure_cmake()
        cmake.build()
    
    def package(self):
        self.copy("LICENSE.txt", dst="licenses", src=self._source_subfolder)
        cmake = self.configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
    
    def package_info(self):
        # self.cpp_info.libs = tools.collect_libs(self)
        # bindir = os.path.join(self.package_folder, "bin")
        # self.output.info(
        #     'Appending PATH environment variable: {}'.format(bindir))
        # self.env_info.PATH.append(bindir)
        # TODO: glslang exports non-namespaced targets but without config file...
        # OSDependent
        self.cpp_info.components["osdependent"].names["cmake_find_package"] = "OSDependent"
        self.cpp_info.components["osdependent"].names["cmake_find_package_multi"] = "OSDependent"
        self.cpp_info.components["osdependent"].libs = [self._get_decorated_lib("OSDependent")]
        if self.settings.os == "Linux":
            self.cpp_info.components["osdependent"].system_libs.append("pthread")
        # OGLCompiler
        self.cpp_info.components["oglcompiler"].names["cmake_find_package"] = "OGLCompiler"
        self.cpp_info.components["oglcompiler"].names["cmake_find_package_multi"] = "OGLCompiler"
        self.cpp_info.components["oglcompiler"].libs = [self._get_decorated_lib("OGLCompiler")]
        # GenericCodeGen
        self.cpp_info.components["genericcodegen"].names["cmake_find_package"] = "GenericCodeGen"
        self.cpp_info.components["genericcodegen"].names["cmake_find_package_multi"] = "GenericCodeGen"
        self.cpp_info.components["genericcodegen"].libs = [self._get_decorated_lib("GenericCodeGen")]
        # MachineIndependent
        self.cpp_info.components["machineindependent"].names["cmake_find_package"] = "MachineIndependent"
        self.cpp_info.components["machineindependent"].names["cmake_find_package_multi"] = "MachineIndependent"
        self.cpp_info.components["machineindependent"].libs = [self._get_decorated_lib("MachineIndependent")]
        self.cpp_info.components["machineindependent"].requires = ["oglcompiler", "osdependent", "genericcodegen"]
        # glslang
        self.cpp_info.components["glslang-core"].names["cmake_find_package"] = "glslang"
        self.cpp_info.components["glslang-core"].names["cmake_find_package_multi"] = "glslang"
        self.cpp_info.components["glslang-core"].libs = [self._get_decorated_lib("glslang")]
        if self.settings.os == "Linux":
            self.cpp_info.components["glslang-core"].system_libs.extend(["m", "pthread"])
        self.cpp_info.components["glslang-core"].requires = ["oglcompiler", "osdependent", "machineindependent"]
        # SPIRV
        self.cpp_info.components["spirv"].names["cmake_find_package"] = "SPIRV"
        self.cpp_info.components["spirv"].names["cmake_find_package_multi"] = "SPIRV"
        self.cpp_info.components["spirv"].libs = [self._get_decorated_lib("SPIRV")]
        self.cpp_info.components["spirv"].requires = ["glslang-core"]
        if self.options.enable_optimizer:
            self.cpp_info.components["spirv"].requires.append("spirv-tools::spirv-tools-opt")
            self.cpp_info.components["spirv"].defines.append("ENABLE_OPT")
        # HLSL
        if self.options.hlsl:
            self.cpp_info.components["hlsl"].names["cmake_find_package"] = "HLSL"
            self.cpp_info.components["hlsl"].names["cmake_find_package_multi"] = "HLSL"
            self.cpp_info.components["hlsl"].libs = [self._get_decorated_lib("HLSL")]
            self.cpp_info.components["glslang-core"].requires.append("hlsl")
            self.cpp_info.components["glslang-core"].defines.append("ENABLE_HLSL")
        # SPVRemapper
        if self.options.spv_remapper:
            self.cpp_info.components["spvremapper"].names["cmake_find_package"] = "SPVRemapper"
            self.cpp_info.components["spvremapper"].names["cmake_find_package_multi"] = "SPVRemapper"
            self.cpp_info.components["spvremapper"].libs = [self._get_decorated_lib("SPVRemapper")]
        
        if self.options.build_executables:
            bin_path = os.path.join(self.package_folder, "bin")
            self.output.info("Appending PATH environment variable: {}".format(bin_path))
            self.env_info.PATH.append(bin_path)
    
    def _get_decorated_lib(self, name):
        libname = name
        if self.settings.os == "Windows" and self.settings.build_type == "Debug":
            libname += "d"
        return libname
#
# class GlslangConan(ConanFile):
#     name = "glslang"
#     version = "master-tot"
#     description = "Khronos-reference front end for GLSL/ESSL, partial front " \
#                   "end for HLSL, and a SPIR-V generator."
#     license = ["BSD-3-Clause", "NVIDIA"]
#     topics = ("conan", "glslang", "glsl", "hlsl", "spirv", "spir-v", "validation", "translation")
#     homepage = "https://github.com/KhronosGroup/glslang"
#     url = "https://github.com/conan-io/conan-center-index"
#     exports_sources = ["CMakeLists.txt", "conanize.patch"]
#     generators = "cmake"
#     settings = "os", "arch", "compiler", "build_type"
#     # short_paths = True
#     options = {
#         "shared": [True, False],
#         "fPIC": [True, False],
#         "build_executables": [True, False],
#         "spv_remapper": [True, False],
#         "hlsl": [True, False],
#         "enable_optimizer": [True, False]
#     }
#     default_options = {
#         "shared": False,
#         "fPIC": True,
#         "build_executables": True,
#         "spv_remapper": True,
#         "hlsl": True,
#         "enable_optimizer": True
#     }
#
#     _cmake = None
#
#     @property
#     def _source_subfolder(self):
#         return "source_subfolder"
#
#     @property
#     def _build_subfolder(self):
#         return "build_subfolder"
#
#     def config_options(self):
#         if self.settings.os == "Windows":
#             del self.options.fPIC
#
#     def configure(self):
#         if self.options.shared:
#             del self.options.fPIC
#         if self.settings.compiler.cppstd:
#             tools.check_min_cppstd(self, 11)
#         if self.options.shared and self.settings.os in ["Windows", "Macos"]:
#             raise ConanInvalidConfiguration("Current glslang shared library build is broken on Windows and Macos")
#
#     def requirements(self):
#         if self.options.enable_optimizer:
#             self.requires("spirv-tools/v2020.3")
#
#     def source(self):
#         tools.get(f"{self.homepage}/archive/3ee5f2f1d3316e228916788b300d786bb574d337.tar.gz")
#         os.rename(self.name + "-" + "3ee5f2f1d3316e228916788b300d786bb574d337", self._source_subfolder)
#
#     def build(self):
#         self._patches_sources()
#         cmake = self._configure_cmake()
#         cmake.build()
#
#     def _patches_sources(self):
#         tools.patch(base_path=self._source_subfolder, patch_file="conanize.patch")
#         # Do not force PIC if static (but keep it if shared, because OGLCompiler and OSDependent are still static)
#         if not self.options.shared:
#             cmake_files_to_fix = [
#                 {"target": "OGLCompiler", "relpath": os.path.join("OGLCompilersDLL", "CMakeLists.txt")},
#                 {"target": "SPIRV", "relpath": os.path.join("SPIRV", "CMakeLists.txt")},
#                 {"target": "SPVRemapper", "relpath": os.path.join("SPIRV", "CMakeLists.txt")},
#                 {"target": "OSDependent", "relpath": os.path.join("glslang", "OSDependent", "Unix", "CMakeLists.txt")},
#                 {"target": "OSDependent",
#                  "relpath": os.path.join("glslang", "OSDependent", "Windows", "CMakeLists.txt")},
#                 {"target": "HLSL", "relpath": os.path.join("hlsl", "CMakeLists.txt")},
#             ]
#             for cmake_file in cmake_files_to_fix:
#                 tools.replace_in_file(os.path.join(self._source_subfolder, cmake_file["relpath"]),
#                                       "set_property(TARGET {} PROPERTY POSITION_INDEPENDENT_CODE ON)".format(
#                                           cmake_file["target"]),
#                                       "")
#             tools.replace_in_file(os.path.join(self._source_subfolder, os.path.join("glslang", "CMakeLists.txt")),
#                                   """set_target_properties(glslang PROPERTIES
#     FOLDER glslang
#     POSITION_INDEPENDENT_CODE ON""",
#                                   """set_target_properties(glslang PROPERTIES
#     FOLDER glslang""")
#
#     def _configure_cmake(self):
#         if self._cmake:
#             return self._cmake
#         self._cmake = CMake(self)
#         self._cmake.definitions["BUILD_EXTERNAL"] = False
#         self._cmake.definitions["SKIP_GLSLANG_INSTALL"] = False
#         self._cmake.definitions["ENABLE_SPVREMAPPER"] = self.options.spv_remapper
#         self._cmake.definitions["ENABLE_GLSLANG_BINARIES"] = self.options.build_executables
#         self._cmake.definitions["ENABLE_GLSLANG_JS"] = False
#         self._cmake.definitions["ENABLE_GLSLANG_WEBMIN"] = False
#         self._cmake.definitions["ENABLE_GLSLANG_WEBMIN_DEVEL"] = False
#         self._cmake.definitions["ENABLE_EMSCRIPTEN_SINGLE_FILE"] = False
#         self._cmake.definitions["ENABLE_EMSCRIPTEN_ENVIRONMENT_NODE"] = False
#         self._cmake.definitions["ENABLE_HLSL"] = self.options.hlsl
#         self._cmake.definitions["ENABLE_RTTI"] = False
#         self._cmake.definitions["ENABLE_OPT"] = self.options.enable_optimizer
#         self._cmake.definitions["ENABLE_PCH"] = True
#         self._cmake.definitions["ENABLE_CTEST"] = False
#         self._cmake.definitions["USE_CCACHE"] = False
#         self._cmake.configure(build_folder=self._build_subfolder)
#         return self._cmake
#
#     def package(self):
#         self.copy("LICENSE.txt", dst="licenses", src=self._source_subfolder)
#         cmake = self._configure_cmake()
#         cmake.install()
#         tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
#
#     def package_info(self):
#         # TODO: glslang exports non-namespaced targets but without config file...
#         # OSDependent
#         self.cpp_info.components["osdependent"].names["cmake_find_package"] = "OSDependent"
#         self.cpp_info.components["osdependent"].names["cmake_find_package_multi"] = "OSDependent"
#         self.cpp_info.components["osdependent"].libs = [self._get_decorated_lib("OSDependent")]
#         if self.settings.os == "Linux":
#             self.cpp_info.components["osdependent"].system_libs.append("pthread")
#         # OGLCompiler
#         self.cpp_info.components["oglcompiler"].names["cmake_find_package"] = "OGLCompiler"
#         self.cpp_info.components["oglcompiler"].names["cmake_find_package_multi"] = "OGLCompiler"
#         self.cpp_info.components["oglcompiler"].libs = [self._get_decorated_lib("OGLCompiler")]
#         # glslang
#         self.cpp_info.components["glslang-core"].names["cmake_find_package"] = "glslang"
#         self.cpp_info.components["glslang-core"].names["cmake_find_package_multi"] = "glslang"
#         self.cpp_info.components["glslang-core"].libs = [self._get_decorated_lib("glslang")]
#         if self.settings.os == "Linux":
#             self.cpp_info.components["glslang-core"].system_libs.extend(["m", "pthread"])
#         self.cpp_info.components["glslang-core"].requires = ["oglcompiler", "osdependent"]
#         # SPIRV
#         self.cpp_info.components["spirv"].names["cmake_find_package"] = "SPIRV"
#         self.cpp_info.components["spirv"].names["cmake_find_package_multi"] = "SPIRV"
#         self.cpp_info.components["spirv"].libs = [self._get_decorated_lib("SPIRV")]
#         self.cpp_info.components["spirv"].requires = ["glslang-core"]
#         if self.options.enable_optimizer:
#             self.cpp_info.components["spirv"].requires.append("spirv-tools::spirv-tools-opt")
#             self.cpp_info.components["spirv"].defines.append("ENABLE_OPT")
#         # HLSL
#         if self.options.hlsl:
#             self.cpp_info.components["hlsl"].names["cmake_find_package"] = "HLSL"
#             self.cpp_info.components["hlsl"].names["cmake_find_package_multi"] = "HLSL"
#             self.cpp_info.components["hlsl"].libs = [self._get_decorated_lib("HLSL")]
#             self.cpp_info.components["glslang-core"].requires.append("hlsl")
#             self.cpp_info.components["glslang-core"].defines.append("ENABLE_HLSL")
#         # SPVRemapper
#         if self.options.spv_remapper:
#             self.cpp_info.components["spvremapper"].names["cmake_find_package"] = "SPVRemapper"
#             self.cpp_info.components["spvremapper"].names["cmake_find_package_multi"] = "SPVRemapper"
#             self.cpp_info.components["spvremapper"].libs = [self._get_decorated_lib("SPVRemapper")]
#
#         if self.options.build_executables:
#             bin_path = os.path.join(self.package_folder, "bin")
#             self.output.info("Appending PATH environment variable: {}".format(bin_path))
#             self.env_info.PATH.append(bin_path)
#
#     def _get_decorated_lib(self, name):
#         libname = name
#         if self.settings.os == "Windows" and self.settings.build_type == "Debug":
#             libname += "d"
#         return libname
