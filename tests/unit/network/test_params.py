from moovi.network.params import flatten_params


def test_flattens_lists() -> None:
    assert flatten_params({"courseids": [1, 2]}) == {
        "courseids[0]": "1",
        "courseids[1]": "2",
    }


def test_flattens_nested_dicts_and_bools() -> None:
    assert flatten_params(
        {"options": [{"name": "onlyactive", "value": True}]}
    ) == {
        "options[0][name]": "onlyactive",
        "options[0][value]": "1",
    }


def test_omits_none_values() -> None:
    assert flatten_params({"courseid": 101, "groupid": None}) == {
        "courseid": "101"
    }


def test_empty_params() -> None:
    assert flatten_params({}) == {}
