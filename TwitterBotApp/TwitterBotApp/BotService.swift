import Foundation

@MainActor
class BotService: ObservableObject {
    static let shared = BotService()

    private var baseURL: String {
        UserDefaults.standard.string(forKey: "botBaseURL") ?? "http://localhost:5000"
    }

    func generateTweet() async throws -> String {
        let url = URL(string: "\(baseURL)/generate")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let response = try JSONDecoder().decode(GenerateResponse.self, from: data)
        return response.tweet
    }

    func postTweet() async throws -> PostResponse {
        var request = URLRequest(url: URL(string: "\(baseURL)/post")!)
        request.httpMethod = "POST"
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(PostResponse.self, from: data)
    }

    func getTopics() async throws -> [String] {
        let url = URL(string: "\(baseURL)/topics")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let response = try JSONDecoder().decode(TopicsResponse.self, from: data)
        return response.topics
    }

    func updateTopics(_ topics: [String]) async throws {
        var request = URLRequest(url: URL(string: "\(baseURL)/topics")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["topics": topics])
        _ = try await URLSession.shared.data(for: request)
    }

    func getConfig() async throws -> ConfigResponse {
        let url = URL(string: "\(baseURL)/config")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(ConfigResponse.self, from: data)
    }

    func updateConfig(intervalHours: Int) async throws {
        var request = URLRequest(url: URL(string: "\(baseURL)/config")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["interval_hours": intervalHours])
        _ = try await URLSession.shared.data(for: request)
    }
}
