from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import TextArea, Markdown
from textual.containers import Vertical
from textual.reactive import reactive

class NoteEditor(Widget):
    view_markdown = reactive(False)
    _content = reactive("")

    def compose(self) -> ComposeResult:
        self.notes_container = Vertical(id="notes-container")
        yield self.notes_container

    def toggle_view_markdown(self):
        self.view_markdown = not self.view_markdown
        

    def update_content(self, content: str):
        self._content = content
        self.notes_container.remove_children()
        if self.view_markdown:
            self.notes_container.mount(Markdown(content))
        else:
            ta = TextArea()
            ta.load_text(content)
            self.notes_container.mount(ta)

    def get_content(self) -> str:
        self._content = self.notes_container.query_one(TextArea).text
        return self._content

    def watch_view_markdown(self, view_markdown: bool):
        if len(self.notes_container.children) > 0:
            if  view_markdown:
                self._content = self.notes_container.children[0].text
            self.update_content(self._content)

class NoteEditorApp(App):
    def compose(self) -> ComposeResult:
        yield NoteEditor()

    def on_mount(self):
        editor = self.query_one(NoteEditor)
        editor.update_content("This is a sample note.")

if __name__ == "__main__":
    NoteEditorApp().run()
