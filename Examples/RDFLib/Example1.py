"""
.. module:: Example1

Example1
******

:Description: Example1

Ejemplos de RDFLIB

"""

from __future__ import print_function
from rdflib.namespace import RDF, RDFS, Namespace, FOAF, OWL
from rdflib import Graph, BNode, Literal
from pprint import pformat
__author__ = 'bejar'

g = Graph()

n = Namespace('http://ejemplo.org/')

p1 = n.persona1
p2 = n.persona2
p3 = n.persona3
v = Literal(22)
v2 = Literal(24)
v3 = Literal(22)
g.add((p1, FOAF.age, v))
g.add((p2, FOAF.age, v2))
g.add((p3, FOAF.age, v3))
# g.serialize('a.rdf')

for a, b, c in g:
    print(a, b, c)

for a, b in g[p1]:
    print(a, b)

t = g.triples((None, FOAF.age, Literal(22)))

for a in t:
    print(a)

