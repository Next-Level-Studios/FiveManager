from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
USER_FACING_FILES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "src" / "fivemanager" / "wizard.py",
    PROJECT_ROOT / "src" / "fivemanager" / "cli.py",
]
CASUAL_PHRASES = [
    "goblin",
    "haunted",
    "violence",
    "diesel",
    "petrol",
    "Radical idea",
    "Modern-ish",
    "wrangling",
    "explode",
    "monument",
]


def test_user_facing_copy_is_clear_and_professional():
    combined = "\n".join(path.read_text() for path in USER_FACING_FILES)
    for phrase in CASUAL_PHRASES:
        assert phrase not in combined


def test_readme_command_list_includes_current_public_commands():
    readme = (PROJECT_ROOT / "README.md").read_text()
    for command in [
        "fivemanager --artifact",
        "fivemanager update-runtime --artifact",
        "fivemanager add",
        "fivemanager self-update --dry-run",
        "fivemanager self-update --prerelease",
    ]:
        assert command in readme
