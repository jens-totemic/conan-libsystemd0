import os
from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.client.tools.oss import get_gnu_triplet

class DebianDependencyConan(ConanFile):
    name = "libsystemd0"
    version = "229"
    build_version = "4ubuntu21.27" 
    homepage = "https://packages.ubuntu.com/xenial-updates/libsystemd0"
    # dev_url = https://packages.ubuntu.com/xenial-updates/libsystemd-dev
    description = "Systemd is a suite of basic building blocks for a Linux system. It provides a system and service manager that runs as PID 1 and starts the rest of the system."
    url = "https://github.com/jens-totemic/conan-libsystemd0"    
    license = "LGPL"
    settings = "os", "arch"

    def requirements(self):
        if self.settings.os == "Linux":
            # todo: we should also add depdencies to libselinux.so.1, liblzma.so.5, libgcrypt.so.20
            # right now this is handled by telling the linker to ignore unknown symbols in secondary dependencies
            self.requires("libudev1/237@totemic/stable")

    def translate_arch(self):
        arch_string = str(self.settings.arch)
        # ubuntu does not have v7 specific libraries
        if (arch_string) == "armv7hf":
            return "armhf"
        elif (arch_string) == "armv8":
            return "arm64"
        elif (arch_string) == "x86_64":
            return "amd64"
        return arch_string
        
    def _download_extract_deb(self, url, sha256):
        filename = "./download.deb"
        deb_data_file = "data.tar.xz"
        tools.download(url, filename)
        tools.check_sha256(filename, sha256)
        # extract the payload from the debian file
        self.run("ar -x %s %s" % (filename, deb_data_file))
        os.unlink(filename)
        tools.unzip(deb_data_file)
        os.unlink(deb_data_file)

    def triplet_name(self):
        # we only need the autotool class to generate the host variable
        autotools = AutoToolsBuildEnvironment(self)

        # construct path using platform name, e.g. usr/lib/arm-linux-gnueabihf/pkgconfig
        # if not cross-compiling it will be false. In that case, construct the name by hand
        return autotools.host or get_gnu_triplet(str(self.settings.os), str(self.settings.arch), self.settings.get_safe("compiler"))
        
    def build(self):
        if self.settings.os == "Linux":
            if self.settings.arch == "x86_64":
                # https://packages.ubuntu.com/xenial-updates/amd64/libsystemd0/download
                sha_lib = "34d152b347b7275161369f1987d0ece1d0245d4d30f9401b71d360c1a5df3101"
                # https://packages.ubuntu.com/xenial-updates/amd64/libsystemd-dev/download
                sha_dev = "0e36146ac9b724c03abcdae63db8de8054bd3f3a38259d79976897a23f9ee267"
                
                url_lib = ("http://us.archive.ubuntu.com/ubuntu/pool/main/s/systemd/libsystemd0_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://us.archive.ubuntu.com/ubuntu/pool/main/s/systemd/libsystemd-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            elif self.settings.arch == "armv8":
                # https://packages.ubuntu.com/xenial-updates/arm64/libsystemd0/download
                sha_lib = "48ea357fff1231011ff311b616352bdf787eddb5ff7770890f67d7fdaa6214f7"
                # https://packages.ubuntu.com/xenial-updates/arm64/libsystemd-dev/download
                sha_dev = "7f465179ec3de83d31c9babcd033386894e82b6da67e95b8368e028b32a0d255"
                
                url_lib = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd0_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            else: # armv7hf
                # https://packages.ubuntu.com/xenial-updates/armhf/libsystemd0/download
                sha_lib = "d09c8b48c283c100f764b5d46dc15b09aa20607ade9e8407d7b80ce3de4dadd6"
                # https://packages.ubuntu.com/xenial-updates/armhf/libsystemd-dev/download
                sha_dev = "4a1d8727ea87df5d6a61da4b7d81b623c208c3467fadc5948855d94aadf68c14"
                
                url_lib = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd0_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            self._download_extract_deb(url_lib, sha_lib)
            self._download_extract_deb(url_dev, sha_dev)
            # remove libsystemd.so which is an absolute link to /lib/aarch64-linux-gnu/libsystemd.so.0.14.0
            libsystemd_so_path = "usr/lib/%s/libsystemd.so" % self.triplet_name()
            os.remove(libsystemd_so_path)
            os.symlink("libsystemd.so.0.14.0", libsystemd_so_path)
        else:
            # We allow using systemd on all platforms, but for anything except Linux nothing is produced
            # this allows unconditionally including this conan package on all platforms
            self.output.info("Nothing to be done for this OS")

    def package(self):
        self.copy(pattern="*", dst="lib", src="lib/" + self.triplet_name(), symlinks=True)
        self.copy(pattern="*", dst="lib", src="usr/lib/" + self.triplet_name(), symlinks=True)
        self.copy(pattern="*", dst="include", src="usr/include", symlinks=True)
        self.copy(pattern="copyright", src="usr/share/doc/" + self.name, symlinks=True)

    def copy_cleaned(self, source, prefix_remove, dest):
        for e in source:
            if (e.startswith(prefix_remove)):
                entry = e[len(prefix_remove):]
                if len(entry) > 0 and not entry in dest:
                    dest.append(entry)

    def package_info(self):
        pkgpath =  "lib/pkgconfig"
        pkgconfigpath = os.path.join(self.package_folder, pkgpath)
        if self.settings.os == "Linux":
            self.output.info("package info file: " + pkgconfigpath)
            with tools.environment_append({'PKG_CONFIG_PATH': pkgconfigpath}):
                pkg_config = tools.PkgConfig("libsystemd", variables={ "prefix" : self.package_folder } )

                # if self.settings.compiler == 'gcc':
                #     # Allow executables consuming this package to ignore missing secondary dependencies at compile time
                #     # needed so we can use libsystemd.so withouth providing a couple of secondary library dependencies
                #     # http://www.kaizou.org/2015/01/linux-libraries.html
                #     self.cpp_info.exelinkflags.extend(['-Wl,--unresolved-symbols=ignore-in-shared-libs'])

                self.output.info("lib_paths %s" % self.cpp_info.lib_paths)

                # exclude all libraries from dependencies here, they are separately included
                self.copy_cleaned(pkg_config.libs_only_l, "-l", self.cpp_info.libs)
                self.output.info("libs: %s" % self.cpp_info.libs)

                self.output.info("include_paths: %s" % self.cpp_info.include_paths)
