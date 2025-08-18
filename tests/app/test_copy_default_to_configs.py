import app.startup as utils


def test_copy_default_to_configs_copies_missing(tmp_path, monkeypatch):
    base = tmp_path / "appdir"
    defaults = base / "defaults"
    configs = base / "configs"
    defaults.mkdir(parents=True)
    configs.mkdir(parents=True)

    # create two files in defaults
    (defaults / "layout.yml").write_text("layout: default")
    (defaults / "bookmarks_bar.json").write_text("[]")

    # create one file in configs to simulate existing file
    (configs / "bookmarks_bar.json").write_text("[\nexisting\n]")

    # point utils.pwd to our temporary base
    monkeypatch.setattr(utils, "pwd", base)

    # replace logger with a fake recorder so we can assert messages
    class FakeLogger:
        def __init__(self):
            self.records = []

        def info(self, msg):
            self.records.append(msg)

    fake_logger = FakeLogger()
    monkeypatch.setattr(utils, "logger", fake_logger)

    utils.copy_default_to_configs()

    # layout.yml should be copied, bookmarks_bar.json should remain (not overwritten)
    assert (configs / "layout.yml").exists()
    assert (configs / "bookmarks_bar.json").read_text().startswith("[")

    # ensure logger recorded the copy message
    assert any("File layout.yml copied successfully" in m for m in fake_logger.records)


def test_copy_default_to_configs_noop_when_none_missing(tmp_path, monkeypatch):
    base = tmp_path / "appdir2"
    defaults = base / "defaults"
    configs = base / "configs"
    defaults.mkdir(parents=True)
    configs.mkdir(parents=True)

    # create same file in both defaults and configs
    (defaults / "layout.yml").write_text("layout: default")
    (configs / "layout.yml").write_text("layout: existing")

    monkeypatch.setattr(utils, "pwd", base)

    # replace logger
    class FakeLogger:
        def __init__(self):
            self.records = []

        def info(self, msg):
            self.records.append(msg)

    fake_logger = FakeLogger()
    monkeypatch.setattr(utils, "logger", fake_logger)

    utils.copy_default_to_configs()

    assert any("No files copied from" in m for m in fake_logger.records)
