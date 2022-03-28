import cherrypy

class HelloMGH(object):
    @cherrypy.expose
    def index(self):
        return 'Hello master MGH27'


if __name__ == "__main__":
    cherrypy.quickstart(HelloMGH)