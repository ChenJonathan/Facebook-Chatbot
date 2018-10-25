from command import *
from util import *

_notes = load_state("Notes")


def _note_handler(author, text, thread_id, thread_type):
    if text.lower() == "clear":
        if thread_id in _notes:
            del _notes[thread_id]
        reply = "Notes have been cleared for this chat."
    elif len(text):
        _notes[thread_id] = text
        reply = "Notes have been updated for this chat!"
    elif thread_id in _notes:
        reply = "<<Note>>\n{}".format(_notes[thread_id])
    else:
        reply = "Notes have not been set for this chat."
    client.send(Message(reply), thread_id, thread_type)
    save_state("Notes", _notes)
    return True


_note_info = """<<Note>>
*Usage*: "!note"
Displays the note for this chat.

*Usage*: "!note <note>"
Sets the note for this chat to <note>.

*Usage*: "!note clear"
Clears the note for this chat."""

map_user_command(["note", "n"], _note_handler, 0, _note_info)
map_group_command(["note", "n"], _note_handler, 0, _note_info)
