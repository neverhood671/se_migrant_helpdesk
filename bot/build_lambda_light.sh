test -f model.zip && rm model.zip
test -f se_migrant_help_bot.zip && rm se_migrant_help_bot.zip

pip3 install --platform manylinux2014_x86_64 --python 3.9 --only-binary=:all: requests -t ./
find ./ -type f -name "*.so" | xargs -r strip
find ./ -type f -name "*.pyc" | xargs -r rm
find ./ -type d -name "__pycache__" | xargs -r rm -r
find ./ -type d -name "*.dist-info" | xargs -r rm -r
find ./ -type d -name "tests" | xargs -r rmx -r

mv topics_modelling.py topics_modelling_heavy.py
mv topics_modelling_light.py topics_modelling.py

zip -r se_migrant_help_bot.zip ./ -x "README.md" -x ".idea/**" -x "*.iml" -x "se_migrant_*.zip" -x "*.sh" -x "model_test.py"

mv topics_modelling.py topics_modelling_light.py
mv topics_modelling_heavy.py topics_modelling.py
