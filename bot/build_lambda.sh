pip3 install requests -t ./
test -f se_migrant_help_bot.zip && rm se_migrant_help_bot.zip
zip -r se_migrant_help_bot.zip ./ -x "README.md" -x "*.iml" -x "*.zip" -x "build_lambda.sh"
