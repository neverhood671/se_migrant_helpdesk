pip3 install requests -t ./
pip3 install scikit-learn -t ./
pip3 install cPickle -t ./
find ./ -type f -name "*.so" | xargs -r strip
find ./ -type f -name "*.pyc" | xargs -r rm
find ./ -type d -name "__pycache__" | xargs -r rm -r
find ./ -type d -name "*.dist-info" | xargs -r rm -r
find ./ -type d -name "tests" | xargs -r rmx -r