from mailer.main import run_mailer


def test_run_mailer():
    result = run_mailer()

    assert result
