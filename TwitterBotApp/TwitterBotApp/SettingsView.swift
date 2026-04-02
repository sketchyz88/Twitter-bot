import SwiftUI

struct SettingsView: View {
    @AppStorage("botBaseURL") private var baseURL = "http://localhost:5000"
    @State private var intervalHours = 4
    @State private var isLoading = false
    @State private var isSaving = false
    @State private var statusMessage = ""

    var body: some View {
        NavigationView {
            Form {
                Section("Backend") {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Python Bot URL")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("http://localhost:5000", text: $baseURL)
                            .autocapitalization(.none)
                            .keyboardType(.URL)
                            .disableAutocorrection(true)
                    }
                }

                Section("Schedule") {
                    Stepper(
                        "Post every \(intervalHours) hour\(intervalHours == 1 ? "" : "s")",
                        value: $intervalHours,
                        in: 1...24
                    )
                }

                Section {
                    Button(action: saveConfig) {
                        if isSaving {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            Text("Save Settings")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(isSaving)
                }

                if !statusMessage.isEmpty {
                    Section {
                        Text(statusMessage)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Settings")
            .onAppear { loadConfig() }
        }
    }

    private func loadConfig() {
        Task {
            do {
                let config = try await BotService.shared.getConfig()
                intervalHours = config.interval_hours
            } catch {
                // non-critical — use default
            }
        }
    }

    private func saveConfig() {
        isSaving = true
        Task {
            do {
                try await BotService.shared.updateConfig(intervalHours: intervalHours)
                statusMessage = "Settings saved."
            } catch {
                statusMessage = "Failed to save: \(error.localizedDescription)"
            }
            isSaving = false
        }
    }
}
