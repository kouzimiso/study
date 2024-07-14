#!/bin/bash

set -e

# Define paths and variables
LIBFFI_VERSION="3.4.2"
LIBFFI_DIR="$HOME/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/armeabi-v7a__ndk_target_21/libffi"
BUILD_DIR="$HOME/study"
LIBFFI_ARCHIVE="libffi-$LIBFFI_VERSION.tar.gz"
LIBFFI_SRC_DIR="$BUILD_DIR/libffi-$LIBFFI_VERSION"
NDK_PATH="/home/kouzimiso/android-ndk/android-ndk-r25"
BUILDOZER_SPEC="$BUILD_DIR/buildozer.spec"

# Function to create buildozer.spec
create_buildozer_spec() {
    cat <<EOL > $BUILDOZER_SPEC
[app]
title = My Application
source.dir = .
package.name = myapp
version = 0.1
p4a.prebuild = ./prebuild.sh

[requirements]
requirements = python3,kivy
EOL
}

# Ask user for action on existing buildozer.spec
if [ -f $BUILDOZER_SPEC ]; then
    read -p "buildozer.spec already exists. Do you want to (d)elete and recreate or (k)eep the existing file? (d/k): " choice
    if [[ "$choice" == "d" ]]; then
        echo "Deleting and recreating buildozer.spec"
        rm $BUILDOZER_SPEC
        create_buildozer_spec
    elif [[ "$choice" == "k" ]]; then
        echo "Keeping the existing buildozer.spec"
    else
        echo "Invalid choice. Exiting."
        exit 1
    fi
else
    create_buildozer_spec
fi

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
export LD_LIBRARY_PATH=$LIBFFI_DIR/lib:$LD_LIBRARY_PATH

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

# Build with Buildozer and save output to a log file
buildozer android debug > build_output.log 2>&1
cp /home/kouzimiso/study/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/libffi/arm64-v8a__ndk_target_21/libffi/config.log ./config.log

