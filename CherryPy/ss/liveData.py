import cherrypy
from walrus import *
import base64


class LiveData(object):
    @cherrypy.expose
    def LD(self, InstrumentID):
        x = rd.hgetall(InstrumentID)
        x = { y.decode('UTF-8'): x.get(y).decode('UTF-8') for y in x.keys() }
        data = json.dumps(x)
        return data





if __name__ == '__main__':
  # radis connection
  rd = Database(host="192.168.231.20", port=6379, db=7)
  cherrypy.quickstart(LiveData())