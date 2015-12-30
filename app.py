#!/usr/bin/env python

import json
import time
from flask import Flask, g, flash, request, redirect, render_template, make_response, url_for

links_file = "./links.json"

app = Flask("goto")
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

def has_link(name):
    return any(l['name'] == name for l in g.links)

def find_link(name):
    found = [l for l in g.links if l['name'] == name]
    if len(found) == 1:
        return found[0]
    else:
        return None

def timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())

@app.before_request
def before_request():
    g.links = load_links()

@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

@app.route("/", methods=["POST"])
def add_or_update_link():
    name = request.form["name"].strip()
    url = request.form["url"].strip()

    link = find_link(name)
    if link:
        link['url'] = request.form["url"]
        link['date'] = timestamp()
        link['visits'] = 0
        save_links(g.links)
        flash(u"Updated link '{name}' to {url}".format(**locals()), "success")
        return redirect(url_for("index"), code=200)
    else:
        g.links.append({
            "name": name,
            "url": url,
            "date": timestamp(),
            "visits": 0
        })
        save_links(g.links)
        flash(u"Added link from '{name}' to {url}".format(**locals()), "success")
        return redirect(url_for("index"), code=201)

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
    if link:
        g.links = [l for l in g.links if l['name'] != name]
        save_links(g.links)
        flash(u"Deleted link {} to {}".format(link['name'], link['url']), "error")
        return make_response(render_template('index.html', name=name), 200)
    else:
        flash(u"The link {} doesn't even exist, cannot delete it".format(name), "error")
        return make_response(render_template('index.html', name=name), 404)

if __name__ == "__main__":
    app.run()
