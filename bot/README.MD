Build the package: `npm run build`

Create a Lambda function using the .zip deployment package:
`aws lambda create-function --function-name hello-world --runtime "nodejs16.x" --role <EXECUTION_ROLE_ARN> --zip-file "fileb://dist/index.zip" --handler index.handler`


Run a test event to confirm that the function returns the following response. If you want to invoke this function using API Gateway, create and configure a REST API:
```
{
    "statusCode": 200,
    "body": "{\"message\":\"hello world\"}"
}
```