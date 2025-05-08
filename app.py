# app.py
from textual.app import App
from screens.list_screen import ProblemListScreen
from screens.detail_screen import ProblemDetailScreen
from database import ProblemDatabase

class ProblemTrackerApp(App):
    CSS_PATH = "styles/app.tcss"
    DB_PATH = "problems.db"
    SCREENS = {
        "list": ProblemListScreen,
        "detail": lambda slug, name: ProblemDetailScreen(slug, name),
    }

    def on_mount(self):
        self.database = ProblemDatabase(db_path=self.DB_PATH)
        self.database.init_db()
        self.push_screen("list")

if __name__ == "__main__":
    ProblemTrackerApp().run()

