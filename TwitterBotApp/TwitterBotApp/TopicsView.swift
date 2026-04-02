import SwiftUI

struct TopicsView: View {
    @State private var topics: [String] = []
    @State private var isLoading = false
    @State private var isSaving = false
    @State private var newTopic = ""
    @State private var errorMessage = ""

    var body: some View {
        NavigationView {
            List {
                Section("Current Topics") {
                    ForEach(topics, id: \.self) { topic in
                        Text(topic)
                    }
                    .onDelete(perform: deleteTopic)
                }

                Section("Add Topic") {
                    HStack {
                        TextField("New topic…", text: $newTopic)
                        Button("Add") {
                            addTopic()
                        }
                        .disabled(newTopic.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                }

                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }
            .navigationTitle("Topics")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Save") { saveTopics() }
                    }
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    EditButton()
                }
            }
            .onAppear { loadTopics() }
            .overlay {
                if isLoading {
                    ProgressView("Loading…")
                        .padding()
                        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                }
            }
        }
    }

    private func loadTopics() {
        isLoading = true
        Task {
            do {
                topics = try await BotService.shared.getTopics()
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }

    private func saveTopics() {
        isSaving = true
        Task {
            do {
                try await BotService.shared.updateTopics(topics)
                errorMessage = ""
            } catch {
                errorMessage = error.localizedDescription
            }
            isSaving = false
        }
    }

    private func addTopic() {
        let trimmed = newTopic.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        topics.append(trimmed)
        newTopic = ""
    }

    private func deleteTopic(at offsets: IndexSet) {
        topics.remove(atOffsets: offsets)
    }
}
