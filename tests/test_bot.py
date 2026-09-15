import asyncio
import json
import threading
import time
from base64 import urlsafe_b64encode
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot as module
from bot import HTTPError, NetworkError, TastyCo, cli


def token(exp):
    payload = urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=")
    return f"header.{payload}.signature"


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.delenv("TASTYCO_CAPTCHA_KEY", raising=False)
    monkeypatch.delenv("TASTYCO_REF_CODE", raising=False)
    # Any accidentally unmocked request fails locally; tests never contact services.
    monkeypatch.setattr(
        module.cloudscraper,
        "create_scraper",
        MagicMock(side_effect=AssertionError("Network disabled")),
    )


@pytest.fixture
def app(tmp_path):
    return TastyCo(tmp_path)


def configure(app):
    (app.config_dir / "accounts.txt").write_text("01" * 32 + "\n", encoding="utf-8")
    (app.config_dir / "sctg.txt").write_text("test-key\n", encoding="utf-8")
    (app.config_dir / "useragent.txt").write_text("Mozilla/5.0 test\n", encoding="utf-8")


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "invalid",
        "a.!.b",
        token(None),
        token("123"),
        token(True),
        token(float("inf")),
        token(-1),
    ],
)
def test_invalid_token_is_expired(app, value):
    app.accounts[1] = {"access_token": value}
    assert app.decode_token(1) == 0


def test_valid_token_and_token_response(app):
    expiry = int(time.time()) + 3600
    app.accounts[1] = {}
    assert not app.store_tokens(1, {"tokens": None})
    assert app.store_tokens(
        1, {"tokens": {"access_token": token(expiry), "refresh_token": token(expiry)}}
    )
    assert app.decode_token(1) == expiry
    assert not app.store_tokens(1, {"tokens": {"access_token": "bad"}})


def test_env_captcha_precedes_file(app, monkeypatch):
    configure(app)
    monkeypatch.setenv("TASTYCO_CAPTCHA_KEY", "env-key")
    assert app.load_captcha_key() == "env-key"


def test_user_agents_reload_and_missing_file(app):
    configure(app)
    app.load_user_agents()
    app.load_user_agents()
    assert app.user_agents == ["Mozilla/5.0 test"]
    (app.config_dir / "useragent.txt").unlink()
    app.load_user_agents()
    assert app.user_agents == []


def test_default_config_dir_is_project_config():
    assert TastyCo().config_dir == module.Path(module.__file__).resolve().parent / "config"


def test_user_agents_accept_indented_profile_data_and_dedupe(app):
    (app.config_dir / "useragent.txt").write_text(
        "UA String:\n  Mozilla/5.0 profile\nHTTP User-Agent:\n  Mozilla/5.0 profile\n",
        encoding="utf-8",
    )
    app.load_user_agents()
    assert app.user_agents == ["Mozilla/5.0 profile"]


def test_missing_user_agents_fails_before_network(app):
    configure(app)
    (app.config_dir / "useragent.txt").write_text("invalid", encoding="utf-8")
    app.process_accounts = AsyncMock()
    assert asyncio.run(app.main(once=True, use_proxy=False)) == 1
    app.process_accounts.assert_not_awaited()


def test_no_proxy_fallback_when_list_empty(app):
    app.USE_PROXY = True
    app.check_connection = AsyncMock()
    assert asyncio.run(app.process_check_connection(1)) is False
    app.check_connection.assert_not_awaited()


def test_proxy_rotation_is_bounded(app):
    app.USE_PROXY = app.ROTATE_PROXY = True
    app.proxies = ["one:80", "two:80", "one:80"]
    app.check_connection = AsyncMock(return_value=False)
    assert asyncio.run(app.process_check_connection(1)) is False
    assert app.check_connection.await_count == 2


def test_successful_proxy_is_used_for_login(app):
    app.USE_PROXY = app.ROTATE_PROXY = True
    app.proxies = ["one:80", "two:80"]
    app.accounts[1] = {"access_exp_time": None}
    app.check_connection = AsyncMock(side_effect=[False, True])
    app.login_request = AsyncMock(return_value=None)
    assert asyncio.run(app.process_user_login(1)) is False
    app.login_request.assert_awaited_once_with(1, "http://two:80")


def test_proxy_reload_resets_assignments(app):
    app.proxies = ["old:80"]
    app.get_next_proxy_for_account(1)
    (app.config_dir / "proxy.txt").write_text("new:80\n", encoding="utf-8")
    app.load_proxies()
    assert app.get_next_proxy_for_account(1) == "http://new:80"


def test_request_runs_off_event_loop_and_closes_session(app, monkeypatch):
    session = MagicMock()
    session.__enter__.return_value = session
    session.request.side_effect = lambda *a, **kw: threading.get_ident()
    monkeypatch.setattr(app, "create_scraper", lambda proxy: session)
    worker = asyncio.run(app.request("GET", "https://example.invalid", timeout=1))
    assert worker != threading.get_ident()
    session.__exit__.assert_called_once()


def test_network_errors_redact_credentials(app, monkeypatch):
    session = MagicMock()
    session.__enter__.return_value = session
    session.request.side_effect = ValueError("https://user:secret@host/?token=secret")
    monkeypatch.setattr(app, "create_scraper", lambda proxy: session)
    with pytest.raises(NetworkError) as error:
        asyncio.run(app.request("GET", "https://example.invalid"))
    assert "secret" not in str(error.value)
    session.__exit__.assert_called_once()


def test_http_errors_do_not_include_response_body(app):
    with pytest.raises(HTTPError, match="^HTTP 401$"):
        app.ensure_ok(SimpleNamespace(status_code=401, text="private-token"))


def test_permanent_error_does_not_retry(app):
    app.accounts[1] = {"user_agent": "test", "address": "test"}
    app.request = AsyncMock(return_value=SimpleNamespace(status_code=401))
    assert asyncio.run(app.login_request(1)) is None
    assert app.request.await_count == 1


def test_transient_error_retries(app, monkeypatch):
    app.accounts[1] = {"user_agent": "test", "address": "test"}
    app.request = AsyncMock(
        side_effect=[
            NetworkError("timeout"),
            SimpleNamespace(status_code=200, json=lambda: {"message": "ok"}),
        ]
    )
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())
    assert asyncio.run(app.login_request(1)) == {"message": "ok"}
    assert app.request.await_count == 2


def test_solver_error_is_not_treated_as_token(app):
    app.CAPTCHA["captcha_key"] = "test"
    app.request = AsyncMock(
        side_effect=[
            SimpleNamespace(status_code=200, text="OK|task"),
            SimpleNamespace(status_code=200, text="ERROR|secret"),
        ]
    )
    assert asyncio.run(app.solve_turnstile(retries=1)) is None


def test_failed_quiz_is_safe(app):
    app.missions_quiz_activity = AsyncMock(return_value=None)
    app.missions_reward = AsyncMock()
    assert (
        asyncio.run(app.process_mission(1, {"id": "q", "type": "QUESTION_MARKING", "progress": 0}))
        is False
    )
    app.missions_reward.assert_not_awaited()


@pytest.mark.parametrize("progress", [1, "1", 1.0])
def test_invitation_target_is_checked_before_claim(app, progress):
    app.missions_reward = AsyncMock()
    assert (
        asyncio.run(
            app.process_mission(
                1, {"id": "invite", "type": "INVITE_REAL_USER", "progress": progress, "amount": 5}
            )
        )
        is True
    )
    app.missions_reward.assert_not_awaited()


def test_numeric_progress_claims_regular_reward(app):
    app.missions_reward = AsyncMock(return_value=True)
    assert asyncio.run(app.process_mission(1, {"id": "m", "progress": 1.0, "reward": None})) is True
    app.missions_reward.assert_awaited_once()


def test_malformed_mission_does_not_stop_remaining_missions(app):
    app.process_user_login = AsyncMock(return_value=True)
    app.scoreboard_me = AsyncMock(
        return_value={"user": {"nickname": "test", "telegramProfiles": [1]}, "balance": None}
    )
    app.daily_info = AsyncMock(return_value={"todayClaimed": True})
    app.missions_list = AsyncMock(
        return_value={"data": [{"id": "bad", "progress": None}, {"id": "good", "progress": 1}]}
    )
    app.missions_reward = AsyncMock(return_value=True)
    app.set_invite = AsyncMock()
    assert asyncio.run(app.process_accounts(1)) is False
    app.missions_reward.assert_awaited_once_with(1, "good", None)
    app.set_invite.assert_not_awaited()


def test_once_continues_after_account_failure(app, monkeypatch):
    configure(app)
    (app.config_dir / "accounts.txt").write_text("01" * 32 + "\n" + "02" * 32, encoding="utf-8")
    app.process_accounts = AsyncMock(side_effect=[ValueError("secret"), True])
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())
    assert asyncio.run(app.main(once=True, use_proxy=False)) == 1
    assert app.process_accounts.await_count == 2


def test_once_success_exits_without_scheduler(app):
    configure(app)
    app.process_accounts = AsyncMock(return_value=True)
    assert asyncio.run(app.main(once=True, use_proxy=False)) == 0


def test_rejected_refresh_falls_back_to_login(app):
    expiry = time.time() + 3600
    app.accounts[1] = {"refresh_exp_time": expiry, "access_exp_time": 0}
    app.process_check_connection = AsyncMock(return_value=True)
    app.auth_refresh = AsyncMock(return_value=None)
    app.login_request = AsyncMock(return_value={"message": "test"})
    app.solve_turnstile = AsyncMock(return_value="test-token")
    app.auth_login = AsyncMock(
        return_value={"tokens": {"access_token": token(expiry), "refresh_token": token(expiry)}}
    )
    assert asyncio.run(app.process_user_login(1)) is True
    app.auth_refresh.assert_awaited_once()
    app.auth_login.assert_awaited_once()


def test_valid_token_skips_login(app):
    app.accounts[1] = {"access_exp_time": time.time() + 3600}
    app.process_check_connection = AsyncMock(return_value=True)
    app.login_request = AsyncMock()
    assert asyncio.run(app.process_user_login(1)) is True
    app.login_request.assert_not_awaited()


def test_missing_captcha_key_exits(app):
    configure(app)
    (app.config_dir / "sctg.txt").write_text("\n", encoding="utf-8")
    app.process_accounts = AsyncMock()
    assert asyncio.run(app.main(once=True, use_proxy=False)) == 1
    app.process_accounts.assert_not_awaited()


def test_missing_proxy_file_exits_without_direct_request(app):
    configure(app)
    app.process_accounts = AsyncMock()
    assert asyncio.run(app.main(once=True, use_proxy=True)) == 1
    app.process_accounts.assert_not_awaited()


def test_direct_mode_ignores_environment_proxy(app, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://unwanted-proxy:80")
    session = MagicMock()
    monkeypatch.setattr(module.cloudscraper, "create_scraper", lambda: session)
    assert app.create_scraper().trust_env is False
    session.proxies.update.assert_not_called()


def test_signature_is_recoverable(app):
    app.accounts[1] = {}
    assert app.generate_evm_wallet(1, "01" * 32)
    message = {"message": "offline authentication test"}
    signature = app.generate_signature(1, message)
    recovered = module.Account.recover_message(
        module.encode_defunct(text=message["message"]), signature=signature
    )
    assert recovered == app.accounts[1]["address"]


@pytest.mark.parametrize("hour,minute,day", [(0, 0, 15), (0, 1, 16), (23, 59, 16)])
def test_daily_utc_schedule(app, monkeypatch, hour, minute, day):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 15, hour, minute, tzinfo=timezone.utc)

    monkeypatch.setattr(module, "datetime", FixedDateTime)
    assert app.get_next_run_time() == datetime(2026, 9, day, 0, 1, tzinfo=timezone.utc)


def test_cli_help_and_invalid_flags():
    with pytest.raises(SystemExit) as error:
        cli(["--help"])
    assert error.value.code == 0
    with pytest.raises(SystemExit) as error:
        cli(["--rotate-proxy", "--no-proxy"])
    assert error.value.code == 2


def test_ctrl_c_during_interactive_prompt(monkeypatch):
    monkeypatch.setattr(module.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(TastyCo, "print_question", MagicMock(side_effect=KeyboardInterrupt))
    assert cli([]) == 130
