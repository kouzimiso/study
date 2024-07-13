#!/bin/bash

# Function to find NDK path
find_ndk_path() {
    # Default paths where Buildozer NDK might be located
    local default_paths=(
        "/usr/share/buildozer/android/platform/android-ndk-r*/toolchains/llvm/prebuilt/linux-x86_64/bin/clang"
        "$HOME/.buildozer/android/platform/android-ndk-r*/toolchains/llvm/prebuilt/linux-x86_64/bin/clang"
    )

    local found_path
    for path_pattern in "${default_paths[@]}"; do
        found_path=$(ls $path_pattern 2>/dev/null)
        if [ -n "$found_path" ]; then
            echo "$found_path"
            return 0
        fi
    done

    # NDK not found
    echo "NDK path not found"
    return 1
}

# Create Python test script
cat <<EOF > test.py
def main():
    print("Python script running successfully!")

if __name__ == "__main__":
    main()
EOF

# Create Cython test script
cat <<EOF > test.pyx
def cython_func():
    print("Cython function called successfully!")
EOF

# Compile Cython to C
cythonize test.pyx

# Wait for user input
read -p "Press enter to continue..."

# Clean up test files
rm test.py test.pyx test.c

# Check buildozer version
echo "Buildozer version:"
buildozer --version
echo

# Check Python version
echo "Python version:"
python3 --version
echo

# Check Cython version
echo "Cython version:"
cython --version
echo

# Check NDK version
echo "NDK version at path:"
ndk_path=$(find_ndk_path)
if [ -n "$ndk_path" ]; then
    $ndk_path --version
else
    echo "NDK path not found"
fi

# Wait for user input
read -p "Press enter to continue..."

# Build Android app using Buildozer
buildozer android debug
