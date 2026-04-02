import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            TweetsView()
                .tabItem {
                    Label("Tweets", systemImage: "bird")
                }
            TopicsView()
                .tabItem {
                    Label("Topics", systemImage: "list.bullet")
                }
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
    }
}
