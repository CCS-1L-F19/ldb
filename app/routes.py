import os
import flask
from urllib.parse import quote, unquote
from app.models import Document
from app.ref import build_graph, graph_svg
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
