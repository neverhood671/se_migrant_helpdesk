package reddit_models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PostModel(
    val kind: String,
    val data: PostDataModel
)

@Serializable
data class PostDataModel(
    val after: String? = "",
    val before: String? = "",
    val dist: Int = 0,
    val children: List<PostChildrenModel> = listOf()
)

@Serializable
data class PostChildrenModel(
    val kind: String,
    val data: PostChildrenDataModel
)

@Serializable
data class PostChildrenDataModel(
    val name: String,
    val title: String = "",
    val selftext: String = "",
    @SerialName("crosspost_parent_list") val crosspostParentList: List<PostChildrenDataModel> = listOf()
)
