#!/bin/bash

export PATH="/home/kouzimiso/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH"

cd /home/kouzimiso/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi

./configure --host=arm-linux-androideabi --prefix=/home/kouzimiso/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi --disable-builddir --enable-shared

make

make install
