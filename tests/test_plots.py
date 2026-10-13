"""Score plots repaint by themselves when their data changes, rather than
waiting for an unrelated repaint (a click, a resize)."""

from core.ui.game.plots import PlotView


def test_data_changes_request_a_repaint(qapp, monkeypatch):
    view = PlotView()
    view.addLinePlot()
    requests = []
    monkeypatch.setattr(view.plot, "update", lambda *a: requests.append(a))

    view.addSeries([0, 3, 7], "Ann")
    assert requests, "adding a series must schedule a repaint"

    requests.clear()
    view.clearPlotContents()
    assert requests, "clearing the plot must schedule a repaint"
