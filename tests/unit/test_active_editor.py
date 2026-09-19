from pathlib import Path

from tsse.application.active_editor import EditableFeatureSession, SessionEditorAdapter


class Editor:
    dirty = True

    def save(self, _service, _path):
        self.dirty = False
        return "saved"

    def discard(self):
        self.dirty = False


def test_adapter_delegates_existing_session() -> None:
    adapter: EditableFeatureSession = SessionEditorAdapter(Editor(), object(), Path("game.sii"))  # type: ignore[arg-type]
    assert adapter.is_dirty
    assert adapter.save() == "saved"
    assert not adapter.is_dirty
