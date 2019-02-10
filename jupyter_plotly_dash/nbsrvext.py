'''
Server extension for jupyter-plotly-dash
'''

#
#    nbsrvext.py
#
#    (c) Gibbs Consulting, a division of 0802100 (BC) Ltd, 2018
#
#    This file is part of jupyter-plotly-dash.
#
#    Jupyter-plotly-dash is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Jupyter-plotly-dash is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with jupyter-plotly-dash.  If not, see <https://www.gnu.org/licenses/>.
#

from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler

from notebook.services.kernels.handlers import ZMQChannelsHandler

from traitlets import Instance

from tornado import gen
from tornado.concurrent import Future, future_set_result_unless_cancelled

import json
import uuid

#
# Three comm_message types are used.
# The types are in the 'jpd_type' member of data of any comm_open or comm_msh
# All messages should be intercepted in the server and not passed to the front end
#
# inform: outbound message from kernel, that indicates that the message contains info about a dash application
#                  other data - da_id is the dash application id used by server to route requests
# request: inbound message from server, requesting a particular route for an app
#                  other data - stem is the remainder of the url
# response: outbound message from kernel, containing the response (as a utf-8 string) and associated mime type
#                  other data - response is the response body, as utf-8
#                               mimetype is the mime type of the response
#

current_get = ZMQChannelsHandler.get
current_on_message = ZMQChannelsHandler.on_message
current_on_reply = ZMQChannelsHandler._on_zmq_reply

@gen.coroutine
def wrapped_get(self, kernel_id):
    # TODO wrap in maybe_future
    yield current_get(self, kernel_id)

def wrapped_on_message(self, msg):

    m2 = None

    if isinstance(msg, bytes):
        # for now, ignore binary messages
        pass
    else:
        deser_msg = json.loads(msg)
        channel = deser_msg.get('channel',None)
        header = deser_msg['header']
        msg_type = header.get('msg_type',"")
        if msg_type == 'comm_open' or msg_type == 'comm_msg':
            session = header['session']
            content = deser_msg['content']
            comm_id = content['comm_id']
            target_name = content.get('target_name',None)

            # Message will get sent to kernel. Here we also ensure we have a registration for future use and pull out the initial data info

            h2 = {}
            for k in ['username','session','version',]:
                h2[k] = header[k]
            h2['msg_type'] = 'comm_msg'
            h2['msg_id'] = str(uuid.uuid4()).replace('-','')
            channel = 'shell'
            m2 = {'header':h2,
                  'metadata':{},
                  'channel':channel,
                  'parent_header':{},
                  'buffers':[],
                  'content':{'comm_id':comm_id,
                             'data':{'some':'junky stuff'}}}

            stream = self.channels[channel]
            session = self.session

    com = current_on_message(self, msg)

    if m2:
        session.send(stream, m2)

    return com

def wrapped_on_reply(self, stream, msg_list):
    idents, fed_msg_list = self.session.feed_identities(msg_list)

    # Hunt for a comm_open or comm_msg message

    try:
        loc = fed_msg_list[1].decode('utf-8')
        jLoc = json.loads(loc)
        msg_type = jLoc['msg_type']
        if msg_type[:4] == 'comm':
            pContent = fed_msg_list[4].decode('utf-8')
            jpContent = json.loads(pContent)
            theData = jpContent.get('data',{})
            jpd_type = theData.get('jpd_type','')
            if jpd_type == 'inform':

                # Need to store session, channel, stream, username, session(id in header), version, comm_id
                try:
                    channel = getattr(stream,'channel',None)
                    shell_channel = self.channels['shell'] # need this channel for sending requests to kernel
                    session = self.session
                    username = jLoc['username']
                    session_id = jLoc['session']
                    version = jLoc['version']
                    comm_id = jpContent['comm_id']
                    da_id = theData['da_id']
                except Exception as e:
                    print(e)

                RequestRedirectionHandler.register_comm(da_id,
                                                        {'session':session,
                                                         'channel':channel,
                                                         'shell_channel':shell_channel,
                                                         'username':username,
                                                         'session_id':session_id,
                                                         'version':version,
                                                         'comm_id':comm_id})

                return
            if jpd_type == 'response':
                parLoc = fed_msg_list[2].decode('utf-8')
                jParLoc = json.loads(parLoc)
                corr_id = jParLoc['msg_id']
                future = RequestRedirectionHandler.get_future_for_response(corr_id)
                response = theData['response']
                mimetype = theData['mimetype']
                future_set_result_unless_cancelled(future,(response, mimetype))
                return

    except:
        pass

    return current_on_reply(self, stream, msg_list)

ZMQChannelsHandler.get = wrapped_get
ZMQChannelsHandler.on_message = wrapped_on_message
ZMQChannelsHandler._on_zmq_reply = wrapped_on_reply

class RequestRedirectionHandler(IPythonHandler):

    kernel_manager = Instance('notebook.services.kernels.kernelmanager.MappingKernelManager')

    registered_apps = {}
    registered_comms = {}
    outstanding_responses = {}

    @staticmethod
    def register_comm(da_id, params):
        RequestRedirectionHandler.registered_comms[da_id] = params

    @gen.coroutine
    def get(self, da_id=None, stem=None):
        args = {k:self.get_argument(k) for k in self.request.arguments}
        yield self.send_with_pause(da_id, stem, args, "GET")

    @gen.coroutine
    def post(self, da_id=None, stem=None):
        #args = {k:self.get_argument(k) for k in self.request.arguments}
        args = json.loads(self.request.body.decode('utf-8'))
        yield self.send_with_pause(da_id, stem, args, "POST")

    def check_xsrf_cookie(self):
        # Override for this handler; post permitted as the alternatives with xsrf are too awkward to contemplate
        return

    @gen.coroutine
    def locate_comm(self, da_id, timeout=1, loops=5 ):
        resp = self.registered_comms.get(da_id,None)
        while resp is None and loops > 10:
            loops -= 1
            # TODO need to make this work!
            # A 'get X or wait n seconds and try again' future for extracting registered instances
            yield gen.sleep(timeout)
            resp = self.registered_comms.get(da_id,None)
        return resp

    @staticmethod
    def get_future_for_response(corr_id):
        f = RequestRedirectionHandler.outstanding_responses.get(corr_id, None)
        if f is None:
            # Form a future that gets populated when a response for corr_id is seen
            f = Future() #gen.maybe_future(("some response","text/html"))
            RequestRedirectionHandler.outstanding_responses[corr_id] = f
        return f

    @gen.coroutine
    def send_with_pause(self, da_id, stem, args, src_type):

        #reg_app = RequestRedirectionHandler.registered_apps.get(da_id, {})

        # Construct and send a session message as a Comm
        # and add a future to the list of those waiting for a response from the kernel
        # yield the future to get the response
        comm_bag = yield self.locate_comm(da_id)
        if comm_bag:
            resp = str("Sending for [%s]"%comm_bag)

            corr_id = str(uuid.uuid4()).replace('-','')
            # need a 'yield X or wait n seconds' combo future
            header = { 'username':comm_bag['username'],
                       'session':comm_bag['session_id'],
                       'version':comm_bag['version'],
                       'msg_id':corr_id,
                       'msg_type':'comm_msg',
                }
            msg = {'header':header,
                   'metadata':{},
                   'channel':'shell',
                   'parent_header':{},
                   'buffers':[],
                   'content':{'comm_id':comm_bag['comm_id'],
                              'data':{'jpd_type':'request',
                                      'stem':stem,
                                      'da_id':da_id,
                                      'args':args,
                                      }
                              }
                   }

            comm_bag['session'].send(comm_bag['shell_channel'],
                                     msg)

            response, mime_type = yield self.get_future_for_response(corr_id)
            del self.outstanding_responses[corr_id]

        else:
            response = str('{"re":"RequestRedirectionHandler [%s] [%s] args [%s] from [%s]"}' % (da_id, stem, args, src_type))
            mime_type = "application/json"

        self.write(response)
        self.set_header("Content-Type",mime_type)
        #self.finish()

    @staticmethod
    def register_instance( da_id, args ):

        if da_id is None:
            return str(RequestRedirectionHandler.registered_apps)

        existing = RequestRedirectionHandler.registered_apps.get(da_id, None)

        if not existing:
            RequestRedirectionHandler.registered_apps[da_id] = args
            return "Added: %s" % str(args)

        return "Existing: %s" % str(existing)

class JPDHandler(IPythonHandler):

    def find_args(self):
        aVals = {}
        for arg in ['session_id','kernel_id','local_url',]:
            aVals[arg] = self.get_argument(arg, "<MISSING>")
        return aVals

    def get(self, da_id=None, **kwargs):
        args = self.find_args()
        self.finish(RequestRedirectionHandler.register_instance(da_id, args))

    def post(self, da_id=None, **kwargs):
        args = self.find_args()
        self.finish(RequestRedirectionHandler.register_instance(da_id, args))

def do_load_jupyter_server_extension(nb_app):

    web_app = nb_app.web_app

    host_pattern = '.*$'
    root_endpoint = "/app/"

    web_app.add_handlers(host_pattern,
                         [(url_path_join(web_app.settings['base_url'],
                                         '%(rep)sregister/(?P<da_id>\w+)' %{'rep':root_endpoint} ),
                           JPDHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '%(rep)sregistrants'%{'rep':root_endpoint} ),
                           JPDHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '%(rep)sendpoints/(?P<da_id>\w+)/(?P<stem>.*)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '%(rep)sendpoints/(?P<da_id>\w+)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '/files%(rep)sendpoints/(?P<da_id>\w+)/(?P<stem>.*)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '/files%(rep)sendpoints/(?P<da_id>\w+)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '/api/contents%(rep)sendpoints/(?P<da_id>\w+)/(?P<stem>.*)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '/api/contents%(rep)sendpoints/(?P<da_id>\w+)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          ])

