#!/usr/bin/env python

import os
import signal
import sys

import json
import time

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from flask import Flask, g, flash, request, redirect, render_template, make_response, url_for
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

links_file = "./links.json"

app = Flask(__name__)
app.debug = True
app.secret_key = "not so secret"

def load_links():
    try:
        with open(links_file, "r") as f:
            links = json.load(f)
            return sorted(links, key=lambda link: link['visits'], reverse=True)
    except ValueError:
        return []
    except IOError:
        return []

def save_links(links):
    with open(links_file, "w") as f:
        json.dump(links, f)

def find_link(name):
    found = [l for l in g.links if l['name'] == name]
    if len(found) == 1:
        return found[0]
    else:
        return None

@app.before_request
def before_request():
    g.links = load_links()

@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

@app.route("/", methods=["POST"])
def add_or_update_link():
    name = request.form["name"].strip().lower()
    url = request.form["url"].strip()
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())

    link = find_link(name)
    if link is not None:
        link['url'] = url
        link['date'] = timestamp
        link['visits'] = 0
        save_links(g.links)
        flash(u"Updated link '{name}' to {url}".format(**locals()), "success")
    else:
        g.links.append({
            "name": name,
            "url": url,
            "date": timestamp,
            "visits": 0
        })
        save_links(g.links)
        flash(u"Added link from '{name}' to {url}".format(**locals()), "success")
    
    return redirect(url_for("index"), code=303)

@app.route("/<name>", methods=["GET"])
def goto(name):
    link = find_link(name)
    if link is not None:
        link['visits'] = link['visits'] + 1
        save_links(g.links)
        return redirect(link['url'], code=303)
    else:
        flash(u"That link doesn't exist yet. Create it?", "error")
        return make_response(render_template('index.html', name=name), 404)

@app.route("/<name>", methods=["DELETE"])
def delete_link(name):
    link = find_link(name)
    if link is not None:
        g.links = [l for l in g.links if l['name'] != name]
        save_links(g.links)
        flash(u"Deleted link {} to {}".format(link['name'], link['url']), "error")
        return make_response(render_template('index.html', name=name), 200)
    else:
        flash(u"The link {} doesn't even exist, cannot delete it".format(name), "error")
        return make_response(render_template('index.html', name=name), 404)

@app.route("/opensearch.xml")
def opensearch():
    response = make_response(render_template("opensearch.xml"))
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response

@app.route("/search/suggest/<prefix>")
def suggest(prefix):
    suggestions = [l['name'] for l in g.links if l['name'].lower().startswith(prefix.lower())]
    result = [prefix, suggestions]
    response = make_response(json.dumps(result))
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    response.headers["Content-Type"] = "text/javascript; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="f.txt"'
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Accept-Ranges"] = "none"
    response.headers["Vary"] = "Accept-Encoding"
    return response

def log(message):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
    print "{timestamp} - {message}".format(**locals())

def run_server(opts):
    if opts.data_dir is not None:
        global links_file
        links_file = "{}/links.json".format(opts.data_dir)

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(opts.port)
    log("Server listening on http://0.0.0.0:{}/ (pid: {})".format(opts.port, os.getpid()))

    if opts.pid_file is not None:
        file(opts.pid_file, 'w').write(str(os.getpid()))

    IOLoop.current().start()


def main(argv):
    def on_exit(sig, func=None):
        log("Close application (signal: {})".format(sig))
        IOLoop.current().stop()

    parser = ArgumentParser(
        prog=os.path.basename(__file__),
        description="Simple URL shorterner",
        formatter_class=RawDescriptionHelpFormatter
    )
    parser.add_argument("-d", "--data-dir",
        help="store data in given directory (default: current directory)",
        default=".")
    parser.add_argument("-p", "--port",
        help="set listen port (default: 7410)",
        type=int, default=7410)
    parser.add_argument("-D", "--daemonize",
        help="run server in background (default: run in foreground)",
        action="store_true")
    parser.add_argument("-P", "--pid-file",
        help="where to store pid when daemonizing (default: don't store)")
    parser.add_argument("-w", "--work-dir",
        help="working directory to set when daemonizing (default: current directory)",
        default=".")
    parser.add_argument("-l", "--log-dir",
        help="log directory to set when daemonizing (default: current directory)",
        default=".")

    opts = parser.parse_args()

    signal.signal(signal.SIGTERM, on_exit) # OS says terminate
    signal.signal(signal.SIGINT, on_exit) # ctrl-c

    if opts.daemonize:
        import daemon
        ctx = daemon.DaemonContext(
            working_directory=opts.work_dir,
            initgroups=False,
            stdout=open("{}/stdout.log".format(opts.log_dir), "w"),
            stderr=open("{}/stderr.log".format(opts.log_dir), "w"),
        )
        with ctx:
            run_server(opts)
    else:
        run_server(opts)


if __name__ == "__main__":
    main(sys.argv)
