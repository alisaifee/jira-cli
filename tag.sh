#!/bin/bash 
echo current version:$(python -c "import jiracli;print(jiracli.__version__)")
read -p "new version:" new_version
git tag -s ${new_version} -m "tagging version ${new_version}"
python setup.py build sdist bdist_egg upload


