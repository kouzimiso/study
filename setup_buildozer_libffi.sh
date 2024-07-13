#!/bin/bash
# Download the latest version of libffi from GitHub
wget https://github.com/libffi/libffi/releases/download/v3.4.2/libffi-3.4.2.tar.gz

# Extract the tarball
tar -xzf libffi-3.4.2.tar.gz

# Navigate to the libffi directory
cd libffi-3.4.2

# Configure and install libffi
./configure --prefix=/home/kouzimiso/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi
make
make install

#export PATH="/home/kouzimiso/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH"

#cd /home/kouzimiso/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi
#   \home\kouzimiso\.buildozer\android\platform\build-arm64-v8a_armeabi-v7a\build\other_builds\libffi
#./configure --host=arm-linux-androideabi --prefix=/home/kouzimiso/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi --disable-builddir --enable-shared

#make

#make install
