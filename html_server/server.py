from flask import Flask, request, Response

app = Flask(__name__)
SVG_DATA = {}

@app.route("/")
def index():
    return Response(open("index.html").read(), mimetype="text/html")


@app.route('/current_svg/<id>', methods=['GET'])
def current_svg(id):
    return Response(SVG_DATA[id], mimetype="text/plain")


@app.route('/svg/<id>', methods=['POST'])
def update_svg(id):
    SVG_DATA[id] = request.data.decode("utf-8")
    return "OK"
    
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    
@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
