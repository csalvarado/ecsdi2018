# -*- coding: utf-8 -*-
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

import argparse
from multiprocessing import Process, Queue
import socket

from rdflib import Namespace, Graph, logger, RDF
from flask import Flask, request

from PracticaTienda.utils.ACLMessages import build_message, get_message_properties, get_agent_info, send_message
from PracticaTienda.utils.FlaskServer import shutdown_server
from PracticaTienda.utils.Agent import Agent
from PracticaTienda.utils.OntoNamespaces import ACL
from PracticaTienda.utils.OntologyNamespaces import ECSDI

__author__ = 'Amazon V2'

parser = argparse.ArgumentParser()
parser.add_argument('--open', help="Define si el servidor est abierto al exterior o no", action='store_true',
                    default=False)
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--dhost', default=socket.gethostname(), help="Host del agente de directorio")
parser.add_argument('--dport', type=int, help="Puerto de comunicacion del agente de directorio")

args = parser.parse_args()


# Configuration stuff

if args.port is None:
    port = 9050
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()

if args.dport is None:
    dport = 9000
else:
    dport = args.dport

if args.dhost is None:
    dhostname = socket.gethostname()
else:
    dhostname = args.dhost
hostname = socket.gethostname()
port = 9050

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgenteDevoluciones = Agent('AgenteDevoluciones',
                       agn.AgenteDevoluciones,
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
app = Flask(__name__, template_folder='../templates')

def get_count():
    global messages_cnt
    messages_cnt += 1
    return messages_cnt

@app.route("/comm")
def comunicacion():
    global dsgraph
    global mss_cnt
    gr =  None
    logger.info ('Peticion de info recibida')

    # Extraemos el mensaje que nos envian
    mensaje = request.args['content']
    gm = Graph()
    gm.parse(data=mensaje)

    msgdic = get_message_properties(gm)

    #Comprobacion del mensaje

    if msgdic is None:
        gr = build_message(Graph(), ACL['no_entendido'],sender=AgenteDevoluciones.uri, msgcnt=get_count())
    else:
        performative = msgdic['performative']

        if performative != ACL.request:
            gr = build_message(Graph(), ACL['no_entendido'], sender=AgenteDevoluciones.uri, msgcnt=get_count())

        else:

            content = msgdic['content']
            accion = gm.value(subject=content, predicate=RDF.type)
            #peticion de devolucion
            if accion == ECSDI.Peticion_retorno:
                logger.info("He recibido la peticion de devolucion")

                for item in gm.subjects(RDF.type, ACL.FipaAclMessage):
                    gm.remove((item, None, None))

                gr = gm

                financial = get_agent_info(agn.FinancialAgent, DirectoryAgent, AgenteDevoluciones, get_count())

                gr = send_message(
                    build_message(gr, perf=ACL.request, sender=AgenteDevoluciones.uri, receiver=financial.uri,
                                  msgcnt=get_count(),
                                  content=content), financial.address)

                # No habia ninguna accion en el mensaje
            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=get_count())

    logger.info('Respondemos a la peticion')

    serialize = gr.serialize(format='xml')
    return serialize, 200


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

    """
    pass


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """
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


