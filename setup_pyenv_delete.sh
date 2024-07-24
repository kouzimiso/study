#!/bin/bash

echo "Removing pyenv virtual environments..."
for env in $(pyenv virtualenvs --bare); do
    pyenv uninstall -f $env
done

echo "Removing pyenv..."
rm -rf ~/.pyenv

echo "Cleaning up shell configuration files..."
sed -i '/export PYENV_ROOT="\$HOME\/.pyenv"/d' ~/.bashrc
sed -i '/export PATH="\$PYENV_ROOT\/bin:\$PATH"/d' ~/.bashrc
sed -i '/eval "\$\(pyenv init --path\)"/d' ~/.bashrc
sed -i '/eval "\$\(pyenv virtualenv-init -\)"/d' ~/.bashrc

source ~/.bashrc

echo "pyenv and its virtual environments have been removed."
