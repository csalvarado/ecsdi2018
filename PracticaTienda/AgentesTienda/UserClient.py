"""
Created on Fri Dec 27 15:58:13 2013

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

@author: javier
"""

from __future__ import print_function
from multiprocessing import Process, Queue
import socket

from flask import render_template, Flask, request
from rdflib import Namespace, Graph
from utils.OntologyNamespaces import ACL, ECSDI


from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Agent import Agent
__author__ = 'javier'


# Configuration stuff
hostname = socket.gethostname()
port = 9001

agn = Namespace("http://www.agentes.org/Entidad#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentePersonal = Agent('AgenteSimple',
                       agn.AgenteBuscador,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)

# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__,template_folder='../templates')


@app.route("/")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    return render_template('Initial_page.html')

    pass

@app.route("/cerca", methods=['GET', 'POST'])
def browser_cerca():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """

    global product_list
    if request.method == 'GET':
        return render_template('cerca.html', products=None)
    elif request.method == 'POST':
        # Peticio de cerca
        if request.form['submit'] == 'Cerca':
            logger.info("Enviando peticion de busqueda")

            # Content of the message
            contentResult = ECSDI['Cerca_productes_' + str(get_count())]

            # Graph creation
            gr = Graph()
            gr.add((contentResult, RDF.type, ECSDI.Cerca_productes))

            # Add restriccio nom
            nom = request.form['nom']
            if nom:
                # Subject nom
                subject_nom = ECSDI['RestriccioNom' + str(get_count())]
                gr.add((subject_nom, RDF.type, ECSDI.RestriccioNom))
                gr.add((subject_nom, ECSDI.Nom, Literal(nom, datatype=XSD.string)))
                # Add restriccio to content
                gr.add((contentResult, ECSDI.Restringe, URIRef(subject_nom)))
            marca = request.form['marca']
            if marca:
                subject_marca = ECSDI['Restriccion_Marca_' + str(get_count())]
                gr.add((subject_marca, RDF.type, ECSDI.Restriccion_Marca))
                gr.add((subject_marca, ECSDI.Marca, Literal(marca, datatype=XSD.string)))
                gr.add((contentResult, ECSDI.Restringe, URIRef(subject_marca)))
            min_price = request.form['min_price']
            max_price = request.form['max_price']

            if min_price or max_price:
                subject_preus = ECSDI['Restriccion_Preus_' + str(get_count())]
                gr.add((subject_preus, RDF.type, ECSDI.Rango_precio))
                if min_price:
                    gr.add((subject_preus, ECSDI.Precio_min, Literal(min_price)))
                if max_price:
                    gr.add((subject_preus, ECSDI.Precio_max, Literal(max_price)))
                gr.add((contentResult, ECSDI.Restringe, URIRef(subject_preus)))

            seller = get_agent_info(agn.SellerAgent, DirectoryAgent, UserPersonalAgent, get_count())

            gr2 = send_message(
                build_message(gr, perf=ACL.request, sender=UserPersonalAgent.uri, receiver=seller.uri,
                              msgcnt=get_count(),
                              content=contentResult), seller.address)

            index = 0
            subject_pos = {}
            product_list = []
            for s, p, o in gr2:
                if s not in subject_pos:
                    subject_pos[s] = index
                    product_list.append({})
                    index += 1
                if s in subject_pos:
                    subject_dict = product_list[subject_pos[s]]
                    if p == RDF.type:
                        subject_dict['url'] = s
                    elif p == ECSDI.Marca:
                        subject_dict['marca'] = o
                    elif p == ECSDI.Modelo:
                        subject_dict['modelo'] = o
                    elif p == ECSDI.Precio:
                        subject_dict['precio'] = o
                    elif p == ECSDI.Nombre:
                        subject_dict['nombre'] = o
                    elif p == ECSDI.Peso:
                        subject_dict['peso'] = o
                    product_list[subject_pos[s]] = subject_dict

            return render_template('cerca.html', products=product_list)


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente
    Guardar el grafo en un archivo
    """
    pass


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    """
    a = cola.get()
    a += a

    print(a)
    pass


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')