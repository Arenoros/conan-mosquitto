#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class MosquittoConan(ConanFile):
    name = "mosquitto"
    version = "1.6.12"
    description = "Open source message broker that implements the MQTT protocol"
    url = "https://github.com/bincrafters/conan-mosquitto"
    homepage = "https://mosquitto.org/"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "EPL", "EDL"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt", "mosquitto.patch"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "with_tls": [True, False],
        "with_mosquittopp": [True, False],
        "with_srv": [True, False],
        "with_binaries": [True, False],
        "with_doc": [True, False],
        "with_tls_psk": [True, False], # Include TLS-PSK support (requires WITH_TLS)
        "with_ec": [True, False], # Include Elliptic Curve support (requires WITH_TLS)
        "with_socks": [True, False], # Include SOCKS5 support
        'with_dlt':  [True, False]
    }
    default_options = {
        'shared' : False,
        'fPIC' : True,
        'with_tls' : True,
        'with_tls_psk' : True,
        'with_ec' : True,
        'with_mosquittopp' : False,
        'with_srv' : False,
        'with_binaries' : False,
        'with_doc' : False,
        'with_socks' : True,
        'with_dlt' : False
    }
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"
    def config_options(self):
        if self.settings.os == 'Windows':
            self.options.fPIC = False
        if self.settings.os == "Macos":
            self.options.with_uuid = False

    def configure(self):
        if not self.options.with_mosquittopp:
            del self.settings.compiler.libcxx
        if not self.options.shared:
            self.options.fPIC = False

    def requirements(self):
        if self.options.with_tls:
            self.requires.add("openssl/1.1.1f")
        if self.options.with_srv:
            self.requires.add("c-ares/1.14.0")

    def source(self):
        git = tools.Git(folder=self.source_subfolder)
        git.clone("https://github.com/eclipse/mosquitto.git", 'v1.6.12', shallow=True)
        tools.patch(
            patch_file="mosquitto.patch", base_path=self.source_subfolder)

    def configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["WITH_SRV"]           = "ON" if self.options.with_srv else "OFF"
        cmake.definitions["WITH_BINARIES"] 		= "ON" if self.options.with_binaries else "OFF"
        cmake.definitions["WITH_MOSQUITTOPP"] 	= "ON" if self.options.with_mosquittopp else "OFF"
        cmake.definitions["DOCUMENTATION"] 		= "ON" if self.options.with_doc else "OFF"
        cmake.definitions["WITH_TLS"] 			= "ON" if self.options.with_tls else "OFF"
        cmake.definitions["WITH_TLS_PSK"] 		= "ON" if self.options.with_tls_psk else "OFF"
        cmake.definitions["WITH_EC"] 			= "ON" if self.options.with_ec else "OFF"
        cmake.definitions["WITH_SOCKS"] 		= "ON" if self.options.with_socks else "OFF"
        cmake.definitions["WITH_DLT"]           = "ON" if self.options.with_dlt else "OFF"
        cmake.definitions["WITH_STATIC_LIBRARIES"] = "OFF" if self.options.shared  else "ON"
        if self.settings.os == "Windows":
            cmake.definitions["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = self.options.shared
            cmake.definitions["WITH_THREADING"] = "OFF"
        if self.settings.os == "Linux":
            cmake.definitions["WITH_PIC"] = "ON" if self.options.fPIC else "OFF"
        cmake.configure(build_folder=self.build_subfolder)
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE.txt", dst="licenses", src=self.source_subfolder)
        self.copy(pattern="edl-v10", dst="licenses", src=self.source_subfolder)
        self.copy(pattern="epl-v10", dst="licenses", src=self.source_subfolder)
        cmake = self.configure_cmake()
        cmake.install()

    def deploy(self):
        self.copy("*", src="bin", dst="bin")
        self.copy("*.dll", src="lib", dst="bin")
        self.copy("*.dylib*", src="lib", dst="bin")
        self.copy_deps("*.dylib*", src="lib", dst="bin")
        self.copy_deps("*.dll", src="lib", dst="bin")
        self.copy_deps("*.dll", src="bin", dst="bin")
        self.copy("*.so*", src="lib", dst="bin")
        self.copy_deps("*.so*", src="lib", dst="bin")
        self.copy("mosquitto.conf", src="etc/mosquitto/", dst="bin")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.libs.append("ws2_32")
        elif self.settings.os == "Linux":
            self.cpp_info.libs.extend(["rt", "pthread", "dl"])
