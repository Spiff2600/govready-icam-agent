from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "cleared-identity-copilot"))

from tools import identity_loader  # noqa: E402


def _clear_caches() -> None:
    identity_loader._azure_users.cache_clear()
    identity_loader._aws_users.cache_clear()
    identity_loader._access_reviews.cache_clear()
    identity_loader._personas_text.cache_clear()
    identity_loader.load_all_users.cache_clear()


@pytest.fixture(autouse=True)
def clear_identity_loader_caches():
    _clear_caches()
    yield
    _clear_caches()


def test_load_all_users_with_missing_files(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(identity_loader, "DATA_DIR", tmp_path)

    users = identity_loader.load_all_users()

    assert users == []
    assert identity_loader.get_users_with_weak_mfa() == []
    assert identity_loader.get_service_accounts() == []


@pytest.mark.parametrize(
    "malformed_file",
    [
        "azure_users_roles.json",
        "aws_identity_center_permission_sets.json",
        "privileged_access_reviews.json",
    ],
)
def test_load_all_users_with_single_malformed_file(monkeypatch, tmp_path: Path, malformed_file: str):
    (tmp_path / "azure_users_roles.json").write_text('{"users": []}', encoding="utf-8")
    (tmp_path / "aws_identity_center_permission_sets.json").write_text('{"users": []}', encoding="utf-8")
    (tmp_path / "privileged_access_reviews.json").write_text('{"reviews": []}', encoding="utf-8")
    (tmp_path / malformed_file).write_text("{", encoding="utf-8")
    monkeypatch.setattr(identity_loader, "DATA_DIR", tmp_path)

    assert identity_loader.load_all_users() == []


def test_load_all_users_with_all_malformed_files(monkeypatch, tmp_path: Path):
    (tmp_path / "azure_users_roles.json").write_text("{", encoding="utf-8")
    (tmp_path / "aws_identity_center_permission_sets.json").write_text("{", encoding="utf-8")
    (tmp_path / "privileged_access_reviews.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(identity_loader, "DATA_DIR", tmp_path)

    assert identity_loader.load_all_users() == []
