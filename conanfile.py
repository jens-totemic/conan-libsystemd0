import os
from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.client.tools.oss import get_gnu_triplet

class DebianDependencyConan(ConanFile):
    name = "libsystemd0"
    version = "246"
    build_version = "2ubuntu1"
    homepage = "https://packages.ubuntu.com/bionic-updates/libsystemd0"
    # dev_url = https://packages.ubuntu.com/bionic-updates/libsystemd-dev
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
                # https://packages.ubuntu.com/bionic-updates/amd64/libsystemd0/download
                sha_lib = "26be10202d0b2ab265944d8f20414f6a0de73a86a7a560ac1fa8c90a901c8f24"
                # https://packages.ubuntu.com/bionic-updates/amd64/libsystemd-dev/download
                sha_dev = "7c366124839de5c2ba4443b6c3e52d1067ca79af5de3b493daab1a992fd0d071"

                url_lib = ("http://us.archive.ubuntu.com/ubuntu/pool/main/s/systemd/libsystemd0_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://us.archive.ubuntu.com/ubuntu/pool/main/s/systemd/libsystemd-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            elif self.settings.arch == "armv8":
                # https://packages.ubuntu.com/bionic-updates/arm64/libsystemd0/download
                sha_lib = "b883db0c15c84939cb5be1a57439cf0b47099d7f5063715ee1da4a39cacd817a"
                # https://packages.ubuntu.com/bionic-updates/arm64/libsystemd-dev/download
                sha_dev = "7a3bc5dc1de5f599dd942ac9fa495e6c686e5d89db2ab52210f7bf46834dc27c"

                url_lib = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd0_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            else: # armv7hf
                # https://packages.ubuntu.com/bionic-updates/armhf/libsystemd0/download
                sha_lib = "47bae3683084d42ca49e9fea94c03f552c22499f2e72ffd942cee3aa14c45a5a"
                # https://packages.ubuntu.com/bionic-updates/armhf/libsystemd-dev/download
                sha_dev = "5959d5fd2121956ff29e611ba0617cedff814d7835bdc82613ff68412f5b4073"

                url_lib = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd0_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
                url_dev = ("http://ports.ubuntu.com/ubuntu-ports/pool/main/s/systemd/libsystemd-dev_%s-%s_%s.deb"
                   % (str(self.version), self.build_version, self.translate_arch()))
            self._download_extract_deb(url_lib, sha_lib)
            self._download_extract_deb(url_dev, sha_dev)
            # remove libsystemd.so which is an absolute link to /lib/aarch64-linux-gnu/libsystemd.so.0.14.0
            # libsystemd_so_path = "lib/%s/libsystemd.so" % self.triplet_name()
            # os.remove(libsystemd_so_path)
            # os.symlink("libsystemd.so.0.21.0", libsystemd_so_path)
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
