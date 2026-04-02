import SwiftUI

struct TweetsView: View {
    @State private var previewTweet = ""
    @State private var isGenerating = false
    @State private var isPosting = false
    @State private var statusMessage = ""
    @State private var isSuccess = false

    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Tweet Preview")
                        .font(.headline)
                        .padding(.horizontal)

                    ZStack(alignment: .topLeading) {
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(.systemGray6))
                            .frame(minHeight: 120)
                        if previewTweet.isEmpty {
                            Text("Tap Generate to preview a tweet…")
                                .foregroundColor(.secondary)
                                .padding(12)
                        } else {
                            Text(previewTweet)
                                .padding(12)
                        }
                    }
                    .padding(.horizontal)

                    if !previewTweet.isEmpty {
                        Text("\(previewTweet.count)/280")
                            .font(.caption)
                            .foregroundColor(previewTweet.count > 280 ? .red : .secondary)
                            .frame(maxWidth: .infinity, alignment: .trailing)
                            .padding(.horizontal)
                    }
                }

                HStack(spacing: 16) {
                    Button(action: generateTweet) {
                        Label("Generate", systemImage: "sparkles")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .disabled(isGenerating || isPosting)

                    Button(action: postTweet) {
                        Label("Post Now", systemImage: "paperplane.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(isPosting || isGenerating)
                }
                .padding(.horizontal)

                if isGenerating || isPosting {
                    ProgressView(isGenerating ? "Generating…" : "Posting…")
                }

                if !statusMessage.isEmpty {
                    Label(statusMessage, systemImage: isSuccess ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundColor(isSuccess ? .green : .red)
                        .font(.subheadline)
                }

                Spacer()
            }
            .padding(.top, 24)
            .navigationTitle("Tweet Generator")
        }
    }

    private func generateTweet() {
        isGenerating = true
        statusMessage = ""
        Task {
            do {
                previewTweet = try await BotService.shared.generateTweet()
            } catch {
                statusMessage = "Failed to generate: \(error.localizedDescription)"
                isSuccess = false
            }
            isGenerating = false
        }
    }

    private func postTweet() {
        isPosting = true
        statusMessage = ""
        Task {
            do {
                let response = try await BotService.shared.postTweet()
                previewTweet = response.tweet
                statusMessage = response.success ? "Posted successfully!" : "Post failed."
                isSuccess = response.success
            } catch {
                statusMessage = "Error: \(error.localizedDescription)"
                isSuccess = false
            }
            isPosting = false
        }
    }
}
