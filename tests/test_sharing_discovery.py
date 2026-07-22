# -*- coding: utf-8 -*-
from core.sharing import discovery as D


def test_beacon_roundtrip():
    data = D.encode_beacon('dev1', 'مكتب أ', 48712)
    d = D.decode_beacon(data)
    assert d['id'] == 'dev1' and d['name'] == 'مكتب أ' and d['port'] == 48712


def test_decode_rejects_foreign_packet():
    assert D.decode_beacon(b'random junk') is None
    assert D.decode_beacon(b'{"magic":"OTHER","id":"x","port":1}') is None


def test_peer_table_marks_offline_after_timeout():
    t = D.PeerTable(timeout=10)
    t.update('dev1', 'مكتب أ', '192.168.1.5', 48712, now=100)
    assert len(t.online(now=105)) == 1
    assert len(t.online(now=120)) == 0


def test_peer_table_update_refreshes_last_seen():
    t = D.PeerTable(timeout=10)
    t.update('dev1', 'مكتب أ', '192.168.1.5', 48712, now=100)
    t.update('dev1', 'مكتب أ', '192.168.1.5', 48712, now=118)
    assert len(t.online(now=120)) == 1
