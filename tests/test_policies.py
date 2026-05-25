from app.agent_graph import run_agent


def test_plugin_marketplace_add_command_adds_plugin():
    result = run_agent("/plugin marketplace add forrestchang/andrej-karpathy-skills")

    assert result["intent"] == "plugin_marketplace_add"
    assert result["plugin"] == {
        "name": "forrestchang/andrej-karpathy-skills",
        "source": "marketplace",
        "status": "added",
    }
    assert result["trace"] == [{"tool": "plugin_marketplace_add", "ok": True}]


def test_plugin_marketplace_add_command_requires_owner_repo():
    result = run_agent("/plugin marketplace add")

    assert result["intent"] == "plugin_marketplace_add"
    assert result["message"] == "Usage: /plugin marketplace add <owner/repo>"
    assert result["trace"] == [{"tool": "plugin_marketplace_add", "ok": False}]


def test_plugin_marketplace_add_command_rejects_malformed_plugin_name():
    result = run_agent("/plugin marketplace add ..invalid/-repo")

    assert result["intent"] == "plugin_marketplace_add"
    assert result["message"] == "Usage: /plugin marketplace add <owner/repo>"
    assert result["trace"] == [{"tool": "plugin_marketplace_add", "ok": False}]


def test_plugin_marketplace_add_command_accepts_valid_special_characters():
    result = run_agent("/plugin marketplace add owner-name/repo_name.plugin")

    assert result["intent"] == "plugin_marketplace_add"
    assert result["plugin"] == {
        "name": "owner-name/repo_name.plugin",
        "source": "marketplace",
        "status": "added",
    }
    assert result["trace"] == [{"tool": "plugin_marketplace_add", "ok": True}]


def test_plugin_install_command_installs_from_named_source():
    result = run_agent("/plugin install andrej-karpathy-skills@karapathy-skills")

    assert result["intent"] == "plugin_install"
    assert result["plugin"] == {
        "name": "andrej-karpathy-skills",
        "source": "karapathy-skills",
        "status": "installed",
    }
    assert result["trace"] == [{"tool": "plugin_install", "ok": True}]


def test_plugin_install_command_requires_plugin_and_source():
    result = run_agent("/plugin install andrej-karpathy-skills")

    assert result["intent"] == "plugin_install"
    assert result["message"] == "Usage: /plugin install <plugin>@<source>"
    assert result["trace"] == [{"tool": "plugin_install", "ok": False}]
