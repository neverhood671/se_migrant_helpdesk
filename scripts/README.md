# Some scripts

## [GetAllTopicsFormSubreddit.kt](src/GetAllTopicsFormSubreddit.kt)

Script for collecting topics from Reddit

### How to configure

> __Warning__
> Auth doesn't work if you use two-factor authentication!

1. Create file `src/local_config.properties`
2. Add properties:
```properties
reddit.username=Your real username
reddit.password=Your real user password
reddit.app_id=Your application id
reddit.app_secret=Your application secret
reddit.read.subreddit=Subreddit name
reddit.read.limit=Total number of posts. Min value: 1. Not required. Read all posts if the value is not set.
reddit.read.batchSize=Posts cont for one request. Min value: 1, max value: 100. Not required, default is 100.
reddit.read.sleep-seconds=Sleep seconds. Min value: 1. Not required, default is 10.
```
3. Run script [GetAllTopicsFormSubreddit.kt](src/GetAllTopicsFormSubreddit.kt)
