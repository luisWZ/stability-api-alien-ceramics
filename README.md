## Activate conda

```
conda activate alien-ceramics
```

## Installation

```
brew install pyenv

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

source ~/.zshrc

pyenv install 3.8.18

cd your-project-directory
pyenv local 3.8.18

brew install --cask miniconda

conda create -n alien-ceramics python=3.8
conda activate alien-ceramics

python -m venv venv
source venv/bin/activate

export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1

pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

```
conda create -n alien-ceramics python=3.8
conda activate alien-ceramics
```
