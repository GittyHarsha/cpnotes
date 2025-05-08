# screens/detail_screen.py
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import Button, Header, Label, Switch
from textual import on
from textual.timer import Timer
from pathlib import Path
import logging
from NoteEditor import NoteEditor  # Import the NoteEditor widget

class ProblemDetailScreen(Screen):
    def __init__(self, slug: str, name: str):
        super().__init__()
        self._slug = slug
        self._name = name
        self.note_file = Path("notes") / f"{slug}.md"
        self.save_note_on_solve = False
        self._save_timer = None
        self._time_spent_timer: Timer | None = None  # Timer for tracking time spent
        self._elapsed_time = 0  # Track elapsed time locally
        self._unsaved_time = 0  # Track time since the last database update

    def compose(self):
        yield Header()
        with Horizontal(id="topbar"):
            yield Button(label="← Back", id="back")
            yield Button(label="Open URL", id="open-url")
            yield Button(label="Mark As Solved", id="mark-as-solved", variant="success")
            yield Switch(id="save-note-on-solve", name="save note after solve", value=False, tooltip="save note on solve")
            with Horizontal(id="timer-controls"):
                yield Button(label="Start Timer", id="start-timer", variant="primary", disabled=False)
                yield Button(label="Stop Timer", id="stop-timer", variant="warning", disabled=True)
                yield Button(label="Reset Timer", id="reset-timer", variant="error", disabled=True)
                yield Label("Time Spent: 0s", id="timer-label")
                yield Switch(id="toggle-markdown", name="toggle-markdown", tooltip="toggle markdown view", value=False)
                
        yield NoteEditor(id="note-editor")  # Use NoteEditor instead of TextArea

    def on_mount(self):
        # Ensure notes folder exists
        self.note_file.parent.mkdir(parents=True, exist_ok=True)
        # Load notes into NoteEditor
        note_editor = self.query_one("#note-editor", NoteEditor)
        if self.note_file.exists():
            content = self.note_file.read_text()
            note_editor.update_content(content)
        self.save_note_on_solve = bool(self.app.database.get_save_note_on_solve(self._slug))
        # Set the switch value to match database
        switch = self.query_one("#save-note-on-solve", Switch)
        switch.value = self.save_note_on_solve
        # Load URL from database
        url = self.app.database.get_url(self._slug)
        btn = self.query_one("#open-url", Button)
        btn.disabled = not bool(url)
        self._url = url

        # Load the initial time spent from the database
        self._elapsed_time = self.app.database.get_time_spent(self._slug)
        self.update_timer_label()
        self.update_timer_buttons()

    def update_timer_label(self):
        """
        Update the timer label with the current elapsed time.
        """
        label = self.query_one("#timer-label", Label)
        label.update(f"Time Spent: {self._elapsed_time}s")

    def update_timer_buttons(self):
        """
        Update the enabled/disabled state of timer buttons based on the timer state.
        """
        start_button = self.query_one("#start-timer", Button)
        stop_button = self.query_one("#stop-timer", Button)
        reset_button = self.query_one("#reset-timer", Button)

        if self._time_spent_timer:  # Timer is running
            start_button.disabled = True
            stop_button.disabled = False
            reset_button.disabled = False
        else:  # Timer is stopped
            start_button.disabled = False
            stop_button.disabled = True
            reset_button.disabled = self._elapsed_time == 0

    def increment_time_spent(self):
        """
        Increment the time spent locally and update the label.
        """
        self._elapsed_time += 1
        self._unsaved_time += 1
        self.update_timer_label()

    def save_time_to_database(self):
        """
        Save the unsaved time to the database.
        """
        if self._unsaved_time > 0:
            self.app.database.update_time_spent(self._slug, self._elapsed_time)
            logging.info(f"Saved {self._elapsed_time}s to the database for {self._slug}.")
            self._unsaved_time = 0

    @on(Switch.Changed, "#save-note-on-solve")
    def save_note_on_solve(self, switch: Switch):
        """
        Toggle the save note on solve switch.
        """
        self.save_note_on_solve = switch.value
        if switch.value:
            logging.info("Save note on solve is enabled.")
            self.app.database.update_problem(self._slug, save_note_on_solve=1)
        else:
            logging.info("Save note on solve is disabled.")
            self.app.database.update_problem(self._slug, save_note_on_solve=0)
 
    @on(Switch.Changed, '#toggle-markdown')
    def toggle_markdown(self, switch: Switch):
        """
        Toggle the view between markdown and text.
        """
        note_editor = self.query_one("#note-editor", NoteEditor)
        
        note_editor.toggle_view_markdown()
        self.save_notes()

    @on(Button.Pressed, "#start-timer")
    def start_timer(self):
        """
        Start the timer for tracking time spent.
        """
        if not self._time_spent_timer:
            self._time_spent_timer = self.set_interval(1, self.increment_time_spent)
            logging.info("Timer started.")
        self.update_timer_buttons()

    @on(Button.Pressed, "#stop-timer")
    def stop_timer(self):
        """
        Stop the timer and save the time to the database.
        """
        if self._time_spent_timer:
            self._time_spent_timer.stop()
            self._time_spent_timer = None
            logging.info("Timer stopped.")
        self.save_time_to_database()
        self.update_timer_buttons()

    @on(Button.Pressed, "#reset-timer")
    def reset_timer(self):
        """
        Reset the timer for this problem.
        """
        self.stop_timer()
        self._elapsed_time = 0
        self._unsaved_time = 0
        self.app.database.update_time_spent(self._slug, 0)
        self.update_timer_label()
        self.update_timer_buttons()
        logging.info("Timer reset.")

    @on(Button.Pressed, "#mark-as-solved")
    def mark_as_solved(self):
        self.save_time_to_database()  # Save time before marking as solved
        # Delete note file if save_note_on_solve is False
        if not self.save_note_on_solve and self.note_file.exists():
            try:
                self.note_file.unlink()
                logging.info(f"Note file {self.note_file} deleted as save_note_on_solve is False.")
            except Exception as e:
                logging.error(f"Failed to delete note file: {e}")
        self.app.database.mark_solved(self._slug)  # This should set solved=1, not delete
        logging.info(f"Problem {self._slug} marked as solved in database")
        self.app.pop_screen()

    @on(Button.Pressed, "#back")
    def go_back(self):
        self.save_notes()
        self.save_time_to_database()  # Save time before going back
        self.app.pop_screen()

    @on(Button.Pressed, "#open-url")
    def open_url(self):
        import webbrowser
        if self._url:
            webbrowser.open(self._url)

    def save_notes(self):
        # Ensure notes folder exists
        self.note_file.parent.mkdir(parents=True, exist_ok=True)
        note_editor = self.query_one("#note-editor", NoteEditor)
        content = note_editor.get_content()
        if content:
            self.note_file.write_text(content)
            logging.info(f"Notes saved for {self._name}")

    def on_unmount(self):
        # Stop the time spent timer
        if self._time_spent_timer:
            self._time_spent_timer.stop()
            self._time_spent_timer = None

        # Save the unsaved time to the database
        self.save_time_to_database()
