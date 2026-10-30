import app as mod


def client():
    mod.app.config["TESTING"] = True
    return mod.app.test_client()


def test_health_ok():
    res = client().get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_hello_saluda():
    res = client().get("/hello?name=Ana")
    assert res.status_code == 200
    assert b"Hola, Ana" in res.data


def test_user_existente(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", str(tmp_path / "t.db"))
    mod.init_db()
    res = client().get("/user?id=1")
    assert b"ana" in res.data
