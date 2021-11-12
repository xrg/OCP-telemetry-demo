#!/bin/env python3

from __future__ import annotations

from flask import Flask, jsonify, abort, request
import time

import data

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/dump_internal")
def dum_all_data():
    return jsonify(data.all_hosts)

@app.route("/telemetry/<domain>/<path:profile>/raw")
def test_route(domain, profile):

    if domain != "CSMv1":
        abort(404)

    app.logger.info("Getting data for %s under %s", domain, profile)
    if profile != "some/hosts":
        abort(403)

    tstart = tend = 0
    if request.args.get('latest', False):
        tstart = time.time() - 10.0
        tend = time.time()
    app.logger.info("Getting data from %r to %r", tstart, tend)

    if request.args.get('hosts', False):
        hosts = request.args['hosts'].split(',')
    else:
        hosts = []

    superframe = {
        "domain": "CSMv1",
        "root_profile": profile,
        "time_base": tstart,
        "content": []
        }

    path = "/power/watts"

    host_keys = {f"h{n:04d}": h
                 for n, h in enumerate(hosts)
                 if h in data.all_hosts}

    if not host_keys:
        app.logger.error("No hosts found like %r", hosts)
        abort(404)

    payload = {
        "group": {
            "path": path
            },
        "group_keys": {
            },
        "series": [],
        }

    if len(host_keys) == 1:
        has_keys = False
        payload["group"]["hostname"] = list(host_keys.values())[0]
    else:
        has_keys = True
        for k, h in host_keys.items():
            payload["group_keys"][k] = { "hostname": h}

    for key, hostname in host_keys.items():
        host_data = data.all_hosts[hostname]
        host_ser = host_data[path]
        for s in host_ser:
            if tstart <= s.timestamp <= tend:
                v = { "ts": s.timestamp, "value": s.value}
                if has_keys:
                    v["key"] = key
                payload["series"].append(v)

    payload["series"].sort(key=lambda s: (s["ts"], s.get("key")))

    superframe["content"].append(payload)
    return jsonify(superframe)


@app.route("/telemetry/<domain>/<path:profile>/dimensions")
def test_cfg(domain, profile):
    """Configuration query: this demonstrates retrieving static cfg.
    """

    if domain != "CSMv1":
        abort(404)

    app.logger.info("Getting data for %s under %s", domain, profile)
    if profile != "some/hosts":
        abort(403)

    now = round(time.time(), 2)
    superframe = {
        "domain": "CSMv1",
        "root_profile": profile + '/dimensions',  # TBD!
        "time_base": now,
        "content": []
        }

    payload = {
        "group": {
            "key": "hostname"
            },
        "group_keys": {
            },
        "series": [
            {"ts": now, "hostname": h}
            for h in data.all_hosts
            ],
        }
    superframe["content"].append(payload)

    payload = {
        "group": {
            "key": "path",
            },
        "series": [
            {"ts": now, "path": m.path}
            for m in data.meters_def
            ]
        }
    superframe["content"].append(payload)

    return jsonify(superframe)


data.data_startup()
