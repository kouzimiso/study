#!/bin/bash

# Function to read ndk_path from buildozer.spec
get_ndk_path() {
    ndk_path=$(grep -E '^\s*android.ndk_path\s*=' buildozer.spec | awk -F '=' '{gsub(/ /, "", $2); print $2}')
    echo "$ndk_path"
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

# Read user input
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

# Read NDK path from buildozer.spec
ndk_path=$(get_ndk_path)

# Check NDK version
echo "NDK version at path: $ndk_path"
${ndk_path}/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --version
echo

# Read user input
read -p "Press enter to continue..."

# Build Android app using Buildozer
buildozer android debug
