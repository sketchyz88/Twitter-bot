import Foundation

struct GenerateResponse: Codable {
    let tweet: String
}

struct PostResponse: Codable {
    let tweet: String
    let tweet_id: String?
    let success: Bool
}

struct TopicsResponse: Codable {
    let topics: [String]
}

struct ConfigResponse: Codable {
    let interval_hours: Int
}
