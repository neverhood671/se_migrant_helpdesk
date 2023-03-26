package utils

import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse

class RequestRepeater {
    fun execute(request: () -> HttpRequest): String {
        val client: HttpClient = HttpClient.newBuilder().build()
        var response: HttpResponse<String>
        do {
            response = client.send(request.invoke(), HttpResponse.BodyHandlers.ofString())

            val statusCode = response.statusCode()
            if (statusCode == 200) {
                break
            } else {
                println("Error: $statusCode")
                println("Body: ${response.body()}")
            }
        } while (true)

        return response.body()
    }
}