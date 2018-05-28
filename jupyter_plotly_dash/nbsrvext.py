'''
Server extension for jupyter-plotly-dash
'''

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
    print("In wrapped get")
    yield current_get(self, kernel_id)

def wrapped_on_message(self, msg):

    m2 = None

    if isinstance(msg, bytes):
        # for now, ignore binary messages
        pass
    else:
        deser_msg = json.loads(msg)
        channel = deser_msg.get('channel',None)
        #print("On message, channel is [%s]" % channel)
        header = deser_msg['header']
        msg_type = header.get('msg_type',"")
        if msg_type == 'comm_open' or msg_type == 'comm_msg':
            session = header['session']
            content = deser_msg['content']
            comm_id = content['comm_id']
            target_name = content.get('target_name',None)
            if target_name is not None:
                print("Comm msg with target name [%s]" % target_name)
            print("Comm msg with id [%s] and msg id [%s]" % (comm_id, header.get('msg_id',None)))

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

#In wrapped on reply, channel is [iopub] and type [comm_open]
#[b'comm-348fa2dc3ab040d5b731ed1558a4f914']
#[b'd4bb19e771c068ad9f2be2f0b6822b01b4e2a66c0be3a813c099949b1205b74f', b'{"version":"5.3","date":"2018-05-25T22:58:23.634359Z","session":"5150c95d-adfd68ac54c28dadb5c07d5d","username":"mark","msg_type":"comm_open","msg_id":"29d879f9-ba454246a1932b42b3474fb2"}', b'{"msg_id":"063fc02088274327bf53fbea35a3c07c","username":"username","session":"e2e68a00758c4d61bf439af9300ab4d9","msg_type":"execute_request","version":"5.2","date":"2018-05-25T22:58:23.624863Z"}', b'{}', b'{"data":{"jpd_type":"inform","da_id":"1234abcde"},"comm_id":"348fa2dc3ab040d5b731ed1558a4f914","target_name":"my_comm_target","target_module":null}']
#<jupyter_client.session.Session object at 0x7fc75162c7f0>
#Wrapped_on got a response
#[b'comm-348fa2dc3ab040d5b731ed1558a4f914']
#[b'd795f70a6afc0a6b385e007f91829475aebade40694f93079fcfcdc4cfb3910f', b'{"version":"5.3","date":"2018-05-25T22:58:24.319687Z","session":"5150c95d-adfd68ac54c28dadb5c07d5d","username":"mark","msg_type":"comm_msg","msg_id":"e5a5bae4-31dd6dc2f7ae3ce5657de46e"}', b'{"msg_id":"036ba77e429541858e2be62665dfdb7f","username":"username","session":"e2e68a00758c4d61bf439af9300ab4d9","msg_type":"execute_request","version":"5.2","date":"2018-05-25T22:58:24.312818Z"}', b'{}', b'{"data":{"jpd_type":"response","response":"this is thee response text","mimetype":"text/rubbish"},"comm_id":"348fa2dc3ab040d5b731ed1558a4f914"}']
#<jupyter_client.session.Session object at 0x7fc75162c7f0>


#[b'comm-1ebacdd11ea8412c919086229a0aefe1']
#[b'6d7c546144970f15dcafdd784b81afee3b79218f8e64b17ac19d3f485955ab9e', b'{"version":"5.3","date":"2018-05-25T23:19:38.827992Z","session":"ac5a5074-ecc000ef670d5e3b7a082841","username":"mark","msg_type":"comm_open","msg_id":"6d39841c-977429df12dd49bcdc67d870"}', b'{"username":"","version":"5.2","session":"86ecacdaa685a9a424b1639550acdd26","msg_id":"394f991dc49f124f56120903c0257050","msg_type":"execute_request","date":"2018-05-25T23:19:38.819516Z"}', b'{}', b'{"data":{"jpd_type":"inform","da_id":"cebcd0279de84b95b330064f6466433a"},"comm_id":"1ebacdd11ea8412c919086229a0aefe1","target_name":"jupyter_plotly_dash","target_module":null}']


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

                #print("In wrapped on reply, channel is [%s] and type [%s]" % (channel, msg_type))
                #print("Informed")
                #print(session, channel, shell_channel, username, session_id, version, comm_id, da_id)

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
                print("Wrapped_on got a response")
                print(idents)
                print(fed_msg_list)
                print(self.session)
                parLoc = fed_msg_list[2].decode('utf-8')
                jParLoc = json.loads(parLoc)
                print(jParLoc)
                corr_id = jParLoc['msg_id']
                future = RequestRedirectionHandler.get_future_for_response(corr_id)
                print(corr_id, future)
                response = theData['response']
                mimetype = theData['mimetype']
                future_set_result_unless_cancelled(future,(response, mimetype))
                print("Have set future :",future)
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
        #print("Sending %s to %s" % (reg_app, da_id))

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

            print("Pausing onm responmse for %s"%corr_id)
            response, mime_type = yield self.get_future_for_response(corr_id)
            print("Response")
            print(response, mime_type)
            del self.outstanding_responses[corr_id]
            print("Future deleted")

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

def load_jupyter_server_extension(nb_app):

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

def _jupyter_server_extension_paths():
    return [{
        "module" : "jupyter_plotly_dash.nbsrvext"
        }]
