test -f model.zip && rm model.zip
test -f kommunes.json && rm kommunes.json
cp ../nlp/model.zip ./
cp ../postnummer-kommune-collection/kommunes.json ./

pip3 install --upgrade boto3 -t ./
pip3 install --upgrade requests -t ./
pip3 install --upgrade scikit-learn -t ./
pip3 install --upgrade cPickle -t ./
pip3 install --upgrade pyyaml -t ./
#find ./ -type f -name "*.so" | xargs -r strip
#find ./ -type f -name "*.pyc" | xargs -r rm
#find ./ -type d -name "__pycache__" | xargs -r rm -r
#find ./ -type d -name "*.dist-info" | xargs -r rm -r
#find ./ -type d -name "tests" | xargs -r rmx -r
