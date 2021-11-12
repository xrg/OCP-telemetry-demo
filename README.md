# Minimal CSM-telemetry mock server

This is a minimal server, based on `Flask`, demonstrating the
CSM-telemetry (OCP) API

## Usage

* install requirements: flask
* run it:
  `flask run`
* from another terminal, start requests against it:
  `curl "http://127.0.0.1:5000/telemetry/CSMv1/some/hosts/raw?latest=1&hosts=abc001.example.com,ghi009.example.com" `
