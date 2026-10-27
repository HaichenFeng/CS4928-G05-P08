package com.intellij.ml.llm.template.models.openai

import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import dev.langchain4j.data.message.AiMessage
import dev.langchain4j.data.message.ChatMessage
import dev.langchain4j.data.message.SystemMessage
import dev.langchain4j.data.message.UserMessage
import dev.langchain4j.model.chat.ChatLanguageModel
import dev.langchain4j.model.output.FinishReason
import dev.langchain4j.model.output.Response
import dev.langchain4j.model.output.TokenUsage
import java.net.HttpURLConnection
import java.net.URL

/** Text-only adapter for the pinned SDK, which predates reasoning_effort. */
class Gpt6LunaChatModel(private val apiKey: String, private val temperature: Double) : ChatLanguageModel {
    override fun generate(messages: List<ChatMessage>): Response<AiMessage> {
        val connection = URL("https://api.openai.com/v1/chat/completions").openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "POST"
            connection.connectTimeout = 30000
            connection.readTimeout = 120000
            connection.doOutput = true
            connection.setRequestProperty("Authorization", "Bearer $apiKey")
            connection.setRequestProperty("Content-Type", "application/json")
            val body = requestBody(messages, temperature).toString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { it.write(body) }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (status !in 200..299) {
                val message = try {
                    JsonParser.parseString(text).asJsonObject.getAsJsonObject("error").get("message").asString
                } catch (_: Exception) { "Request failed" }
                throw IllegalStateException("GPT-6 Luna HTTP $status: ${message.replace(apiKey, "[REDACTED]")}")
            }
            return parseResponse(text)
        } finally {
            connection.disconnect()
        }
    }

    companion object {
        fun requestBody(messages: List<ChatMessage>, temperature: Double): JsonObject {
            val array = JsonArray()
            messages.forEach { message ->
                val pair = when (message) {
                    is SystemMessage -> "system" to message.text()
                    is UserMessage -> {
                        require(message.hasSingleText()) { "GPT-6 Luna adapter accepts text-only messages" }
                        "user" to message.singleText()
                    }
                    is AiMessage -> {
                        require(!message.hasToolExecutionRequests()) { "Tool messages are not supported by this adapter" }
                        "assistant" to message.text()
                    }
                    else -> throw IllegalArgumentException("Unsupported chat-message type")
                }
                array.add(JsonObject().apply { addProperty("role", pair.first); addProperty("content", pair.second) })
            }
            return JsonObject().apply {
                addProperty("model", "gpt-6-luna")
                addProperty("reasoning_effort", "none")
                addProperty("temperature", temperature)
                add("messages", array)
            }
        }

        fun parseResponse(text: String): Response<AiMessage> {
            val raw = JsonParser.parseString(text).asJsonObject
            val model = raw.get("model").asString
            require(model == "gpt-6-luna" || model.startsWith("gpt-6-luna-")) { "Unexpected returned model: $model" }
            val choice = raw.getAsJsonArray("choices")[0].asJsonObject
            require(choice.get("finish_reason").asString == "stop") { "Incomplete GPT-6 Luna output" }
            val content = choice.getAsJsonObject("message").get("content")
            require(content != null && !content.isJsonNull) { "Empty GPT-6 Luna response" }
            val usage = raw.getAsJsonObject("usage")
            val tokens = if (usage != null) TokenUsage(usage.get("prompt_tokens").asInt, usage.get("completion_tokens").asInt) else null
            return Response.from(AiMessage.from(content.asString), tokens, FinishReason.STOP, mapOf("model" to model))
        }
    }
}