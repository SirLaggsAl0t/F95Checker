import pathlib

VENDOR = pathlib.Path(__file__).resolve().parents[1] / "vendor"


def _under_vendor(path) -> bool:
    return pathlib.Path(path).resolve().is_relative_to(VENDOR.resolve())


def test_packages_resolve_under_vendor():
    import common
    import external
    import modules
    for pkg in (common, external, modules):
        assert all(_under_vendor(p) for p in pkg.__path__), \
            f"{pkg.__name__} imported from {list(pkg.__path__)}"


def test_core_modules_import_headless():
    import common.structs
    import modules.api
    import modules.db
    for mod in (common.structs, modules.api, modules.db):
        assert _under_vendor(mod.__file__), f"{mod.__name__} imported from {mod.__file__}"
