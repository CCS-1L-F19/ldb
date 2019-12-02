import re
import networkx as nx
import graphviz as gv
from crossref_commons.retrieval import get_publication_as_json as cr_get_pub
from crossref_commons.sampling import get_sample as cr_sample
from app.models import Document
from app import db


def _doi_strip(doi):
    return re.search('10.\d{4,9}/[-._;()/:A-Z0-9]+', doi).group()

 
def get_doc(doi):
    # from crossref website
    d = doi
    try:
        d = _doi_strip(doi)
    except AttributeError:
        # handle this error with a user resp. saying invalid DOI
        pass
    doc = Document.query.filter(Document.doi==d).first()
    if doc is None:
        pub = cr_get_pub(doi)
        doc = Document(doi=d, meta=pub)
        print("Added document {}".format(doc))
        db.session.add(doc)
        db.session.commit()
    return doc


def build_graph(doi, depth=2):
    """
    Returns a graph of the stuff
    """
    graph = nx.DiGraph()
    doc = doi
    if isinstance(doc, list):
        return nx.compose_all([build_graph(d) for d in doc])

    if isinstance(doc, str):
        # this is an initial call, get the publication
        doc = get_doc(doi)
    graph.add_node(doc)
    if depth == 0:
        return graph

    if doc.queried:
        for ref in doc.references:
            graph.add_node(ref)
            graph.add_edge(doc, ref)
            refgraph = build_graph(ref, depth=depth - 1)
            graph = nx.compose(graph, refgraph)
        return graph

    try:
        references = doc['reference']
    except:
        return graph
    for r in references:
        pub = r
        try:
            d = r['DOI']
            if isinstance(d, list):
                d = d[0]
            cites = get_doc(d)
        except (KeyError, IndexError):
            cites = Document(meta=r)
        
        doc.references.append(cites)
        graph.add_node(cites)
        graph.add_edge(doc, cites)
        refgraph = build_graph(cites, depth=depth - 1)
        graph = nx.compose(graph, refgraph)
    doc.queried = True
    db.session.commit()
    return graph
 
 
def graph_svg(graph):
    '''
    Returns an svg string
    '''
    viz = gv.Digraph(format='svg')
    for node in graph.nodes:
        if 'URL' in graph:
            viz.node(str(node), label='<a href="{}">{}</a>'.format(graph['URL'], str(graph)))
        else:
            viz.node(str(node), label=str(node))
    for f, t in graph.edges:
        viz.edge(str(f), str(t))
    return viz.pipe().decode('utf-8')

 
def scrape():
    while True:
        sample = cr_sample(size=50, filter={'type': 'journal-article'})
        for s in sample:
            try:
                doc = Document(doi=s['DOI'], meta=s)
                build_graph(doc)
                db.session.add(doc)
            except (KeyError, ValueError):
                continue
        db.session.commit()
        sleep(30)
