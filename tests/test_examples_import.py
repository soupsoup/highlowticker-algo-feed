import importlib.util
import pathlib

from conftest import make_event

EX = pathlib.Path(__file__).resolve().parent.parent / "examples"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_convenience_strategy_handler_classifies(monkeypatch):
    monkeypatch.setenv("HLT_SYMBOL", "SPY")
    monkeypatch.setenv("HLT_MILESTONE", "5")
    mod = _load(EX / "strategy.py", "ex_strategy")
    strat = mod.Momentum()
    strat(make_event(symbol="SPY", event="new_high", high_count=5, last_price=100.0))
    assert strat.pos == 1 and strat.entry == 100.0
    strat(make_event(symbol="SPY", event="new_low", low_count=1, last_price=101.0))
    assert strat.pos == 0 and round(strat.realized, 2) == 1.0


def test_convenience_notify_send_is_defined():
    mod = _load(EX / "notify.py", "ex_notify")
    assert callable(mod.send)


def test_convenience_notify_filters_highs(monkeypatch):
    monkeypatch.setenv("HLT_MILESTONE", "5")
    monkeypatch.setenv("HLT_SYMBOLS", "aapl, msft")
    mod = _load(EX / "notify.py", "ex_notify_filter")
    assert mod.is_alert(make_event(symbol="AAPL", event="new_high", high_count=5))
    assert mod.is_alert(make_event(symbol="MSFT", event="new_high_and_low", high_count=6))
    assert not mod.is_alert(make_event(symbol="AAPL", event="new_high", high_count=4))
    assert not mod.is_alert(make_event(symbol="TSLA", event="new_high", high_count=9))
    assert not mod.is_alert(make_event(symbol="AAPL", event="new_low", high_count=9))


def test_convenience_notify_alert_survives_send_failure(monkeypatch, capsys):
    mod = _load(EX / "notify.py", "ex_notify_fail")

    def boom(text):
        raise OSError("discord down")

    monkeypatch.setattr(mod, "send", boom)
    mod.alert(make_event(symbol="AAPL", event="new_high", high_count=5))
    assert "send failed for AAPL" in capsys.readouterr().out
