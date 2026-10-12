"""Qwirkle quick-stats columns: the extra headers follow the current language,
and the lowest/total columns are dropped together with their headers."""

from PySide6.QtCore import QCoreApplication, QTranslator


def test_extra_headers_follow_a_language_change(gamedb, qapp):
    from games.qwirkle.widget import QwirkleQSBox

    spanish = QTranslator()
    assert spanish.load(":/i18n/qwirkle_es_ES.qm")
    QCoreApplication.installTranslator(spanish)
    try:
        box = QwirkleQSBox("Qwirkle")
        assert box.tr(box.playerStatsHeaders[-2]) == "Mejor Jug"
    finally:
        QCoreApplication.removeTranslator(spanish)
    # Back in English, the headers translate afresh rather than staying Spanish.
    assert box.tr(box.playerStatsHeaders[-2]) == "Best Play"


def test_columns_and_headers_stay_aligned(gamedb, qapp):
    from games.qwirkle.widget import QwirkleQSBox

    box = QwirkleQSBox("Qwirkle")
    columns = dict(zip(box.playerStatsKeys, box.playerStatsHeaders, strict=True))
    assert "minscore" not in columns and "sumscore" not in columns
    assert columns["maxscore"] == "Highest"
    assert columns["avgscore"] == "Average"
    assert columns["max_round_score"] == "Best Play"
    assert columns["max_qwirkles"] == "Max Qs"
