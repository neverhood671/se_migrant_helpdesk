test -f model.zip && rm model.zip
test -f kommunes.json && rm kommunes.json
test -f se_migrant_help_bot.zip && rm se_migrant_help_bot.zip

cp ../nlp/model.zip ./
cp ../postnummer-kommune-collection/kommunes.json ./

pip3 install --upgrade --platform manylinux2014_x86_64 --python 3.9 --only-binary=:all: requests -t ./
pip3 install --upgrade --platform manylinux2014_x86_64 --python 3.9 --only-binary=:all: scikit-learn -t ./
pip3 install --upgrade --platform manylinux2014_x86_64 --python 3.9 --only-binary=:all: pyyaml -t ./
find ./ -type f -name "*.so" | xargs -r strip
find ./ -type f -name "*.pyc" | xargs -r rm
find ./ -type d -name "__pycache__" | xargs -r rm -r
find ./ -type d -name "*.dist-info" | xargs -r rm -r
find ./ -type d -name "tests" | xargs -r rmx -r

zip -r se_migrant_help_bot.zip ./ -x "README.md" -x "*.iml" -x "se_migrant_*.zip" -x "*.sh" -x "*_test.py"

test -f model.zip && rm model.zip
test -f kommunes.json && rm kommunes.json
