import pytest
import typer

from updatefivem import cli


def test_prepare_service_for_update_stops_after_confirmation(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "_service_is_active", lambda service_name: True)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: True)
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))

    stopped = cli._prepare_service_for_update({"service_name": "fivem-dev"}, assume_yes=False, service_control=True)

    assert stopped is True
    assert calls == [("stop", "fivem-dev")]


def test_prepare_service_for_update_skips_prompt_and_stop_when_service_inactive(monkeypatch):
    calls = []
    prompts = []
    monkeypatch.setattr(cli, "_service_is_active", lambda service_name: False)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: prompts.append(args) or True)
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))

    stopped = cli._prepare_service_for_update({"service_name": "fivem-dev"}, assume_yes=False, service_control=True)

    assert stopped is False
    assert calls == []
    assert prompts == []


def test_prepare_service_for_update_aborts_when_not_ready(monkeypatch):
    monkeypatch.setattr(cli, "_service_is_active", lambda service_name: True)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: False)

    with pytest.raises(typer.Exit):
        cli._prepare_service_for_update({"service_name": "fivem-dev"}, assume_yes=False, service_control=True)


def test_prepare_service_for_update_can_be_skipped(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))

    stopped = cli._prepare_service_for_update({"service_name": "fivem-dev"}, assume_yes=False, service_control=False)

    assert stopped is False
    assert calls == []


def test_offer_start_after_update_asks_even_if_service_was_not_stopped(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "_service_unit_exists", lambda service_name: True)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: True)
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))

    cli._offer_start_after_update(
        {"service_name": "fivem-dev"},
        assume_yes=False,
        service_control=True,
        run_after_update=False,
    )

    assert calls == [("start", "fivem-dev")]


def test_offer_start_after_update_run_option_starts_without_prompt(monkeypatch):
    calls = []
    prompts = []
    monkeypatch.setattr(cli, "_service_unit_exists", lambda service_name: True)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: prompts.append(args) or False)
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))

    cli._offer_start_after_update(
        {"service_name": "fivem-dev"},
        assume_yes=False,
        service_control=True,
        run_after_update=True,
    )

    assert prompts == []
    assert calls == [("start", "fivem-dev")]


def test_offer_start_after_update_prints_command_when_declined(monkeypatch):
    calls = []
    messages = []
    monkeypatch.setattr(cli, "_service_unit_exists", lambda service_name: True)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: False)
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))
    monkeypatch.setattr(cli.console, "print", lambda message: messages.append(str(message)))

    cli._offer_start_after_update(
        {"service_name": "fivem-dev"},
        assume_yes=False,
        service_control=True,
        run_after_update=False,
    )

    assert calls == []
    assert any("updatefivem start" in message for message in messages)
    assert any("systemctl start fivem-dev" in message for message in messages)


def test_offer_start_after_update_skips_prompt_when_service_unit_missing(monkeypatch):
    calls = []
    prompts = []
    messages = []
    monkeypatch.setattr(cli, "_service_unit_exists", lambda service_name: False)
    monkeypatch.setattr(cli.Confirm, "ask", lambda *args, **kwargs: prompts.append(args) or True)
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))
    monkeypatch.setattr(cli.console, "print", lambda message: messages.append(str(message)))

    cli._offer_start_after_update(
        {"service_name": "fivem-dev"},
        assume_yes=False,
        service_control=True,
        run_after_update=True,
    )

    assert calls == []
    assert prompts == []
    assert any("No systemd service named 'fivem-dev' is installed" in message for message in messages)
    assert any("sudo updatefivem service install" in message for message in messages)


def test_offer_start_after_update_does_nothing_when_service_control_disabled(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "_run_service_action", lambda action, service_name: calls.append((action, service_name)))

    cli._offer_start_after_update(
        {"service_name": "fivem-dev"},
        assume_yes=True,
        service_control=False,
        run_after_update=True,
    )

    assert calls == []
