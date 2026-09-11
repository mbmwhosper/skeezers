#!/usr/bin/env python3
"""Regression tests for curated embed probing."""

from probe_curated import content_error, frame_policy_error, identity_error


def main() -> None:
    assert frame_policy_error({"content-security-policy": "frame-ancestors https://other.example"})
    assert frame_policy_error({"content-security-policy": "frame-ancestors https://skeezers.org"}) is None
    assert content_error(b'<meta http-equiv="Content-Security-Policy" content="frame-ancestors \'self\'"><title>Game</title>', "Game")
    assert content_error(b"<html><title>In Progress</title>domain parking</html>", "Game")
    assert content_error(b"<html><title>Correct Game</title><script>play()</script></html>" * 20, "Correct Game") is None
    assert content_error(b"<html><title>Different Game</title><script>play()</script></html>" * 20, "Correct Game")
    assert identity_error(b'{"title":"Paper Minecraft v11.3"}', "Paper Minecraft") is None
    assert identity_error(b'{"title":"Different Project"}', "Paper Minecraft")
    print('{"result":"PASS","probe_policy_tests":8}')


if __name__ == "__main__":
    main()
