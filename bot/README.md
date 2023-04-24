# Python bot for telegram

## Requirements

1. Some cloud account. For now, we have instructions only for AWS, but other clouds have similar functionality.
2. Telegram account

## How to start

### Creating bot in Telegram

Official tutorial: [https://core.telegram.org/bots/tutorial](https://core.telegram.org/bots/tutorial)

1. Write `/newbot` command to main bot [BotFather](https://t.me/BotFather)
2. Write name and username for your bot.

### Add bot token to AWS Secrets Manager

1. Open "AWS Secrets Manager"
2. Select "Store a new secret"
3. Select secret type as "Other type of secret"
4. Enter key `se-migrant-help-bot-token` and put your bot token as value
5. Go "Next" to finish the process

### Creating an API Gateway in AWS

1. Open "API Gateway"
2. Select "Rest API" - "Build"
3. Choose the protocol as "REST" and "create new API" as "New API"
4. Write name for your API, for example: `se_migrant_help_bot_api`
5. Click "Create API"

### Create lambda

1. Open "Lambda"
2. Click "Create Function"
3. Select "Author from scratch"
4. Write name, for example: `se_migrant_help_bot_main`
5. Select runtime "Python 3.9" and Architecture "x86_64"
6. Click "Create Function"
7. For new lambda open tab "Configuration" -> "Environment variables"
8. Add variable `SECRET_REGION_NAME` with your secrets region
8. Add variable `DYNAMODB_REGION_NAME` with your DynamoDB region

### Add code to lambda

1. Look to [How to rebuild](#how-to-rebuild)

### Add permissions for secrets

1. In your lambda open tab "Configuration" -> "Permissions"
2. Open execution role
3. Select "Add permissions -> Create inline policy"
4. Select service "Secrets Manager" and action "GetSecretValue"
5. Select Resources -> Specific -> Any in this account
6. Click "Add additional permission"
7. Select service "KMS" and action "Write->Decrypt"
8. Select Resources -> Specific -> Any in this account
9. Click "Review policy"
10. Enter policy name
11. Click "Create policy"

### Add permissions for DynamoDB

1. In your lambda open tab "Configuration" -> "Permissions"
2. Open execution role
3. Select "Add permissions -> Create inline policy"
4. Select service "Secrets Manager" and action "GetSecretValue"
5. Select Resources -> Specific -> Any in this account
6. Click "Add additional permission"
7. Select service "DynamoDB" and actions:
```
Read
- GetItem
- Query
Write
- CreateTable
- DeleteItem
- PutItem
- UpdateItem
List
- ListTables
```
8. Select Resources -> Specific -> Any in this account
9. Click "Review policy"
10. Enter policy name
11. Click "Create policy"

### Connecting Lambda function to API Gateway

1. Open your API
2. Click "Actions -> Create method -> ANY"
3. In the form enter your lambda functions name
4. Press "Save"
5. Click "Actions -> Deploy API"
6. Select deployment stage as "New stage"
7. Enter any stage name. For example `v1`

### Setting Webhooks

Get your "invoke url", "Bot token" and execute next request:

```
curl -XGET "https://api.telegram.org/bot<your-bot-token>/setWebHook?url=<your-API-invoke-URL>"
```

### Test your bot

Send any message to the bot

### How to rebuild

1. Run script [build_lambda.sh](build_lambda.sh)
2. Open tab "Code" in AWS
3. Click to "Upload from" and select archive "se_migrant_help_bot.zip"
