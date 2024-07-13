#!/bin/bash

set -e

# Define paths
LIBFFI_VERSION="3.4.2"
LIBFFI_DIR="$HOME/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi"
BUILD_DIR="$HOME/study"
LIBFFI_ARCHIVE="libffi-$LIBFFI_VERSION.tar.gz"
LIBFFI_SRC_DIR="$BUILD_DIR/libffi-$LIBFFI_VERSION"
NDK_PATH="/home/kouzimiso/android-ndk/android-ndk-r25"

# Download and extract libffi
cd $BUILD_DIR
if [ ! -f $LIBFFI_ARCHIVE ]; then
    wget https://github.com/libffi/libffi/releases/download/v$LIBFFI_VERSION/$LIBFFI_ARCHIVE
fi

if [ ! -d $LIBFFI_SRC_DIR ]; then
    tar -xzvf $LIBFFI_ARCHIVE
fi

# Build and install libffi
cd $LIBFFI_SRC_DIR
./configure --prefix=$LIBFFI_DIR
make
make install

# Set environment variables
export CFLAGS="-I$LIBFFI_DIR/include"
export LDFLAGS="-L$LIBFFI_DIR/lib"
export PATH=$NDK_PATH/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH

# Verify NDK toolchain
if ! command -v clang >/dev/null 2>&1; then
    echo "Clang not found in the NDK toolchain path. Please verify the NDK path and installation."
    exit 1
fi

# Create prebuild.sh
PREBUILD_SCRIPT="$BUILD_DIR/prebuild.sh"
cat <<EOL > $PREBUILD_SCRIPT
#!/bin/bash
cp -r $LIBFFI_DIR/* $HOME/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/libs/libffi/
EOL
chmod +x $PREBUILD_SCRIPT

# Modify buildozer.spec
BUILDOZER_SPEC="$BUILD_DIR/buildozer.spec"
if ! grep -q "p4a.prebuild" $BUILDOZER_SPEC; then
    echo -e "\n[app]" >> $BUILDOZER_SPEC
    echo "p4a.prebuild = ./prebuild.sh" >> $BUILDOZER_SPEC
fi

if ! grep -q "libffi" $BUILDOZER_SPEC; then
    echo -e "\n[requirements]" >> $BUILDOZER_SPEC
    echo "libffi = $LIBFFI_DIR" >> $BUILDOZER_SPEC
fi

# Build with Buildozer and save output to a log file
cd $BUILD_DIR
buildozer android debug > build_output.log 2>&1
