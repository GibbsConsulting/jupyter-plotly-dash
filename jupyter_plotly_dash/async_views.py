from aiohttp import web
import asyncio

class AsyncViews:
    def __init__(self, port):
        self.port = port
        self.apps = {}

        self.app = web.Application()
        self.app.add_routes([web.get('/{id}/', self.main),
                    web.get('/{id}/_dash-dependencies', self.dependencies),
                    web.get('/{id}/_dash-layout', self.layout),
                    web.post('/{id}/_dash-update-component', self.update),
                    web.get('/{id}/_dash-routes', self.routes),
                   ])

        self.launch_task = asyncio.Task(self.launch_it(self.app, self.port))

    async def launch_it(self, app, port):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()
        return runner, site

    def add_app(self, app, name):
        self.apps[name] = app

    def get_app_by_name(self, name):
        da = self.apps.get(name,None)
        return da, da.as_dash_instance()

    async def main(self, request):
        iden = request.match_info['id']
        da, dapp = self.get_app_by_name(iden)
        mf = dapp.locate_endpoint_function()
        response = mf()
        return web.Response(body=response,
                           content_type="text/html")

    async def dependencies(self, request):
        iden = request.match_info['id']
        da, dapp = self.get_app_by_name(iden)
        with dapp.app_context():
            mFunc = dapp.locate_endpoint_function('dash-dependencies')
            resp = mFunc()
            return web.Response(body=resp.data,
                                content_type=resp.mimetype)

    async def layout(self, request):
        iden = request.match_info['id']
        da, dapp = self.get_app_by_name(iden)
        mFunc = dapp.locate_endpoint_function('dash-layout')
        resp = mFunc()
        body, mimetype = dapp.augment_initial_layout(resp)
        return web.Response(body=body,
                            content_type=mimetype)

    async def update(self, request):

        #rb = json.loads(request.body.decode('utf-8'))
        rb = await request.json()

        iden = request.match_info['id']
        da, dapp = self.get_app_by_name(iden)

        if dapp.use_dash_dispatch():
            # Force call through dash
            mFunc = dapp.locate_endpoint_function('dash-update-component')

            import flask
            with dapp.test_request_context():
                # Fudge request object
                flask.request._cached_json = (rb, flask.request._cached_json[True])
                resp = mFunc()
        else:
            # Use direct dispatch with extra arguments in the argMap
            app_state = da.get_session_state()
            argMap = {}
            argMap = {'dash_app_id': iden,
                      'dash_app': da,
                      'user': None,
                      'session_state': app_state}
            resp = dapp.dispatch_with_args(rb, argMap)
            da.set_session_state(app_state)
            da.handle_current_state()

        return web.Response(body=resp.data,
                            content_type=resp.mimetype)

    async def routes(self, request):
        print("In routes")
        iden = request.match_info['id']
        print("ID is %s"%iden)
        da, dapp = self.get_app_by_name(iden)

gavs = {}

def get_global_av(port=8055):
    global gavs
    gav = gavs.get(port,None)
    if gav is None:
        gav = AsyncViews(port)
        gavs[port] = gav
    return gav
