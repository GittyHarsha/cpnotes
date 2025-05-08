from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ListView, ListItem, Static, Header, SelectionList, Collapsible
from textual.widgets.selection_list import Selection
from textual import on
from textual.reactive import reactive
import logging
from utils import sanitize
from server import TCPServer
import asyncio
from pathlib import Path
logger = logging.getLogger(__name__)

class ProblemListScreen(Screen):
    stack_updates = reactive(0, repaint=False)
    filter_solved = reactive(["unsolved"])  # Default to "unsolved"

    def compose(self):
        yield Header()
        with Horizontal():
            yield Button(label="Start Server", id="toggle")
            with Vertical():
                # Only Solved filter
                with Collapsible(title="Filters"):
                    yield SelectionList[str](
                        Selection("Solved", "solved"),
                        Selection("Unsolved", "unsolved", True),  # Default selected
                        id="solved-filter"
                    )
                yield Static("Problems", classes="title")
                self.list_view = ListView(id="plist")
                yield self.list_view

    def on_mount(self):
        self._server_running = False
        self._tcp_server = TCPServer(callback=self._on_new_problem)
        self._refresh_list()
        self.app.database.register_callback(self._on_database_update)

    @on(SelectionList.SelectedChanged, "#solved-filter")
    def on_solved_filter_changed(self):
        selected = self.query_one("#solved-filter", SelectionList).selected
        if selected:
            self.filter_solved = selected
        else:
            self.filter_solved = None
        self._refresh_list()

    def watch_stack_updates(self) -> None:
        self._refresh_list()

    def _refresh_list(self):
        """Fetch problems and rebuild the ListView."""
        logger.info("Loading problem list")
        filters = {}
        if self.filter_solved is None:
            self.list_view.clear()
            return
        if len(self.filter_solved) > 1:
            pass
        elif self.filter_solved[0] == "solved":
            filters["solved"] = True
        elif self.filter_solved[0] == "unsolved":
            filters["solved"] = False

        items = self.app.database.load_problems(filters)
        self.list_view.clear()
        for pid, name, grp, solved in items:
            mark = "✓" if solved else "✗"
            content = f"{mark} {grp} / {name}"
            card = Static(content, classes="card")
            self.list_view.append(ListItem(card, name=str(pid)))
            logger.debug(f"Added problem to list: {content}")

    @on(Button.Pressed, "#toggle")
    def toggle_server(self):
        btn = self.query_one("#toggle", Button)
        if not self._server_running:
            logger.info("Starting TCP server...")
            asyncio.create_task(self._tcp_server.start())
            btn.label = "Stop Server"
        else:
            logger.info("Stopping TCP server...")
            asyncio.create_task(self._tcp_server.stop())
            btn.label = "Start Server"
        self._server_running = not self._server_running

    def _on_new_problem(self, data: dict):
        """Handle incoming JSON, save it, and refresh."""
        try:
            name = data.get("name")
            grp  = data.get("group")
            url  = data.get("url")
            slug = sanitize(name)
            note_path = Path("notes") / f"{slug}.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure notes folder exists
            note_path.write_text("")
            self.app.database.save_problem(name, grp, url, slug, solved=0, note_path=str(note_path))
        except Exception as e:
            logger.error(f"Error saving problem: {e}")
        self._refresh_list()

    def _on_database_update(self):
        """Callback when database changes externally."""
        logger.info("Database updated, reloading problems...")
        self._refresh_list()

    @on(ListView.Selected)
    def open_detail(self, event: ListView.Selected):
        pid = int(event.item.name)
        result = self.app.database.get_problem(pid)
        if result:
            slug, name, solved, save_note_on_solve = result  # Fetch additional fields
            if solved and not save_note_on_solve:
                # TODO: Inform the user that notes are not available 
                pass
            else:
                # Open the detail screen
                self.app.push_screen(self.app.SCREENS["detail"](slug, name))

    def on_unmount(self):
        if self._server_running:
            asyncio.create_task(self._tcp_server.stop())
            self._server_running = False