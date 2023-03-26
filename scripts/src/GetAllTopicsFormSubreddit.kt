import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import reddit_models.PostModel
import reddit_models.TokenModel
import utils.RequestRepeater
import java.net.URI
import java.net.http.HttpRequest
import java.nio.file.Paths
import java.util.*
import kotlin.io.path.inputStream

class RedditProperties {
    val username: String
    val password: String
    val appId: String
    val appSecret: String
    val readSubreddit: String

    init {
        val properties = Properties()
        properties.load(Paths.get("scripts", "src", "local_config.properties").inputStream())
        this.username = properties.getProperty("reddit.username")
        this.password = properties.getProperty("reddit.password")
        this.appId = properties.getProperty("reddit.app_id")
        this.appSecret = properties.getProperty("reddit.app_secret")
        this.readSubreddit = properties.getProperty("reddit.read.subreddit")
    }
}

fun main() {
    val formatter = Json { ignoreUnknownKeys = true }

    val properties = RedditProperties()
    val requestRepeater = RequestRepeater()
    val basicAuthorization = Base64.getEncoder().encodeToString(
        "${properties.appId}:${properties.appSecret}".toByteArray()
    )

    val response = requestRepeater.execute {
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

    val tokenObj = formatter.decodeFromString<TokenModel>(response)

    val answerBody = requestRepeater.execute {
        HttpRequest.newBuilder()
            .uri(URI.create("https://oauth.reddit.com/r/${properties.readSubreddit}/new"))
            .header("Authorization", "bearer ${tokenObj.accessToken}")
            .GET()
            .build()
    }

    println(answerBody)

    val post = formatter.decodeFromString<PostModel>(answerBody)
    println(post.data.after)
}
