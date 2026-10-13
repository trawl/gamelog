"""Bundled quick-reference rules: lookup, fallback, registry and dialog."""

import dataclasses

import pytest

from core.registry import registry
from core.rules import candidate_locales, load_rules


@pytest.fixture
def qwirkle_without_rules(monkeypatch):
    """Qwirkle with its sheet removed, to cover games that have none."""
    stripped = dataclasses.replace(definition("Qwirkle"), rules_doc=None)
    monkeypatch.setitem(registry._definitions, "Qwirkle", stripped)


def definition(name):
    found = registry.get(name)
    assert found is not None
    return found


def test_candidate_locales_fall_back_to_english():
    assert candidate_locales("es_ES") == ["es_ES", "es", "en_GB"]
    assert candidate_locales(None) == ["en_GB"]
    assert candidate_locales("C") == ["en_GB"]


def test_missing_translation_falls_back_to_english(qapp):
    assert load_rules("catan", "es_ES") == load_rules("catan", "en_GB")


def test_unknown_document_is_none(qapp):
    assert load_rules("no_such_game", "en_GB") is None


def test_every_declared_rules_doc_is_bundled(qapp):
    for definition in registry.definitions():
        if definition.rules_doc:
            text = load_rules(definition.rules_doc)
            assert text, f"{definition.name}: missing rules sheet"


def test_catan_has_rules_and_official_link():
    catan = definition("Catan")
    assert catan.rules_doc == "catan"
    assert (catan.rules_url or "").startswith("https://")


def test_rules_dialog_renders_and_searches(qapp):
    from core.ui.rules import RulesDialog

    dialog = RulesDialog(definition("Catan"))
    assert "Longest Road" in dialog.browser.toPlainText()
    dialog.search("Monopoly")
    assert dialog.browser.textCursor().selectedText() == "Monopoly"


def test_rules_dialog_without_sheet_shows_placeholder(qapp, qwirkle_without_rules):
    from core.ui.rules import RulesDialog

    dialog = RulesDialog(definition("Qwirkle"))
    assert "No rules available" in dialog.browser.toPlainText()


def test_game_tab_rules_button_only_for_documented_games(
    qapp, gamedb, qwirkle_without_rules
):
    catan = registry.create_widget("Catan", ["Ann", "Bob"])
    qwirkle = registry.create_widget("Qwirkle", ["Ann", "Bob"])
    assert not catan.rulesButton.isHidden()
    assert qwirkle.rulesButton.isHidden()
    catan.showRules()
    assert catan.rulesDialog.isVisible()
    first = catan.rulesDialog
    catan.showRules()
    assert catan.rulesDialog is first


def test_new_game_tab_rules_button_follows_selected_game(
    qapp, gamedb, qwirkle_without_rules
):
    from core.ui.newgame import NewGameWidget

    tab = NewGameWidget()
    tab.retranslateUI()
    tab.gameComboBox.setCurrentText("Catan")
    assert tab.rulesButton.isEnabled()
    tab.showRules()
    dialog = tab.rulesDialogs["Catan"]
    assert dialog.isVisible()
    assert "Longest Road" in dialog.browser.toPlainText()
    tab.showRules()
    assert tab.rulesDialogs["Catan"] is dialog

    tab.gameComboBox.setCurrentText("Qwirkle")
    assert not tab.rulesButton.isEnabled()
    assert not tab.rulesButton.isHidden()


def test_every_rules_sheet_has_a_registered_game():
    """Each bundled sheet is wired to a game, so none is silently orphaned."""
    from pathlib import Path

    docs = {d.rules_doc for d in registry.definitions() if d.rules_doc}
    bundled = {
        p.name.removesuffix("_en_GB.md")
        for p in Path("games").glob("*/rules/*_en_GB.md")
    }
    assert bundled == docs


def test_every_rules_sheet_renders_and_links_are_https(qapp):
    from core.ui.rules import RulesDialog

    for definition in registry.definitions():
        if not definition.rules_doc:
            continue
        dialog = RulesDialog(definition)
        assert len(dialog.browser.toPlainText()) > 500, definition.name
        if definition.rules_url:
            assert definition.rules_url.startswith("https://"), definition.name
