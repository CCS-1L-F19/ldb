import os
import flask
from urllib.parse import quote, unquote
from app.models import Document
from app.ref import build_graph, graph_svg, sort_graph
from app import app, db
from app.forms import GraphForm

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = GraphForm()
    if form.validate_on_submit():
        return flask.redirect(flask.url_for('cy', doi=quote(form.doi.data, safe='')))
    return flask.render_template('index.html', form=form)

@app.route('/results/<doi>', methods=['GET'])
def results(doi):
    g = build_graph(unquote(doi))
    s = graph_svg(g)
    return s

@app.route('/cy/<doi>', methods=['GET'])
def cy(doi):
    g = build_graph(unquote(doi))
    return flask.render_template('cy.html', graph=g)
     
 
@app.route('/txt/<doi>', methods=['GET'])
def txt(doi):
    g = build_graph(unquote(doi))
    s = sort_graph(g)
    ref = [a.refstring() for a in s]
    cb = []
    for a in s:
        try:
            cb.append(a['is-referenced-by-count'])
        except KeyError:
            cb.append('?')
    lines = ['{}\t{}'.format(r, c) for r, c in zip(ref, cb)]
    response = flask.make_response('\n'.join(lines))
    response.headers["Content-Disposition"] = "attachment; filename=citegraph.txt"
    return response
