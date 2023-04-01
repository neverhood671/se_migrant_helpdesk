import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import reddit_models.PostChildrenDataModel
import reddit_models.PostModel
import reddit_models.TokenModel
import utils.RequestRepeater
import java.io.File
import java.net.URI
import java.net.http.HttpRequest
import java.nio.file.Paths
import java.util.*
import java.util.concurrent.TimeUnit
import kotlin.io.path.inputStream

class RedditProperties {
    val username: String
    val password: String
    val appId: String
    val appSecret: String
    val readSubreddit: String
    val limit: Int
    val batchSize: Int
    val sleepSeconds: Long

    init {
        val properties = Properties()
        properties.load(Paths.get("scripts", "src", "local_config.properties").inputStream())
        this.username = properties.getProperty("reddit.username")
        this.password = properties.getProperty("reddit.password")
        this.appId = properties.getProperty("reddit.app_id")
        this.appSecret = properties.getProperty("reddit.app_secret")
        this.readSubreddit = properties.getProperty("reddit.read.subreddit")

        this.limit = properties.getProperty("reddit.read.limit")?.toInt() ?: Int.MAX_VALUE
        if (this.limit < 1) {
            throw RuntimeException(
                "Wrong configuration. Property reddit.read.limit less than 1: $limit"
            )
        }

        this.batchSize = properties.getProperty("reddit.read.batchSize")?.toInt() ?: 100
        if (this.batchSize < 1) {
            throw RuntimeException(
                "Wrong configuration. Property reddit.read.batchSize less than 1: $batchSize"
            )
        } else if (this.batchSize > 100) {
            throw RuntimeException(
                "Wrong configuration. Property reddit.read.batchSize more than 100: $batchSize"
            )
        }

        this.sleepSeconds = properties.getProperty("reddit.read.sleep-seconds")?.toLong() ?: 10L
        if (this.sleepSeconds < 1) {
            throw RuntimeException(
                "Wrong configuration. Property reddit.read.sleep-seconds less than 1: $sleepSeconds"
            )
        }
    }
}

data class ReadResult(
    val lastPostId: String = "",
    val error: RuntimeException? = null,
    val posts: List<String>,
    val newPostsNames: Set<String>
)


fun readPages(
    properties: RedditProperties,
    tokenObj: TokenModel,
    before: String,
    postFilter: (PostChildrenDataModel) -> Boolean,
): ReadResult {
    val posts = mutableListOf<String>()
    val newPostsNames = mutableSetOf<String>()

    val addPostAndCount: (PostChildrenDataModel) -> Unit = {
        if (it.selftext.isNotEmpty() && !newPostsNames.contains(it.name) && postFilter(it)) {
            posts.add("${it.title} ${it.selftext}")
            newPostsNames.add(it.name)
        }
    }

    val answerBody = REQUEST_REPEATER.execute {
        HttpRequest.newBuilder()
            .uri(
                URI.create(
                    "https://oauth.reddit.com/r/${properties.readSubreddit}/new?" +
                            "after=$before" +
                            "&limit=${properties.batchSize}"
                )
            )
            .header("Authorization", "bearer ${tokenObj.accessToken}")
            .GET()
            .build()
    }

    val post: PostModel
    try {
        post = FORMATTER.decodeFromString<PostModel>(answerBody)
    } catch (e: RuntimeException) {
        println("Something goes wrong\n\tResponse: $answerBody\n\tError: ${e.message}")
        return ReadResult(error = e, posts = posts, newPostsNames = newPostsNames)
    }

    for (child in post.data.children) {
        addPostAndCount(child.data)

        child.data.crosspostParentList.forEach {
            addPostAndCount(it)
        }
    }
    return ReadResult(
        lastPostId = post.data.children.lastOrNull()?.data?.name ?: "",
        posts = posts,
        newPostsNames = newPostsNames
    )
}

val FORMATTER = Json {
    ignoreUnknownKeys = true
    prettyPrint = true
}
val REQUEST_REPEATER = RequestRepeater()

fun main() {
    val properties = RedditProperties()
    val basicAuthorization = Base64.getEncoder().encodeToString(
        "${properties.appId}:${properties.appSecret}".toByteArray()
    )

    val response = REQUEST_REPEATER.execute {
        HttpRequest.newBuilder()
            .uri(URI.create("https://www.reddit.com/api/v1/access_token"))
            .header("Authorization", "Basic $basicAuthorization")
            .POST(
                HttpRequest.BodyPublishers.ofString(
                    "grant_type=password&username=${properties.username}&password=${properties.password}"
                )
            )
            .build()
    }

    val tokenObj: TokenModel
    try {
        tokenObj = FORMATTER.decodeFromString<TokenModel>(response)
    } catch (e: RuntimeException) {
        println("Response: $response, Error: ${e.message}")
        e.printStackTrace(System.out)
        return
    }

    val allPosts = mutableListOf<String>()
    val readNames = mutableSetOf<String>()
    var lastPostId = ""
    do {
        if (lastPostId.isNotEmpty()) {
            TimeUnit.SECONDS.sleep(properties.sleepSeconds)
        }

        val result = readPages(properties, tokenObj, lastPostId) {
            !readNames.contains(it.name)
        }

        if (result.error == null) {
            lastPostId = result.lastPostId
        }
        allPosts.addAll(result.posts)

        println("Read ${allPosts.size} posts. Sleep for ${properties.sleepSeconds} sec.")
    } while (allPosts.size < properties.limit && (result.posts.isNotEmpty() || result.error != null))

    File("all_posts_${properties.readSubreddit}.json")
        .writeText(
            FORMATTER.encodeToString(
                JsonArray(allPosts.map { JsonPrimitive(it) })
            )
        )
}
