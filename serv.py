import BaseHTTPServer
import json
import redis
import time

class MyHandler( BaseHTTPServer.BaseHTTPRequestHandler ):
    server_version= "FairingFactory/0.2"
    def do_OPTIONS( self ):
        self.log_message( "Command: %s Path: %s Headers: %r"
                          % ( self.command, self.path, self.headers.items() ) )
        self.send_response( 200 )
        self.send_header( "Access-Control-Allow-Origin", "*" )
        self.send_header( "Access-Control-Allow-Methods", "POST, OPTIONS" )
        self.send_header( "Access-Control-Max-Age", "1000" )
        # something not working? find out what was in the header jquery send and add the field here.
        self.send_header( "Access-Control-Allow-Headers", "origin, x-requested-with, content-type, accept" )
        self.end_headers()

    def do_GET( self ):
        self.log_message( "Command: %s Path: %s Headers: %r"
                          % ( self.command, self.path, self.headers.items() ) )
        self.send_error( 405, "GET is not allowed for the fairing factory API. It only accepts POST requests containing json kit orders. See PROTOCOL.md" )
    
    def do_POST( self ):
        self.log_message( "Command: %s Path: %s Headers: %r"
                          % ( self.command, self.path, self.headers.items() ) )
        if self.headers.has_key('content-length'):
            length= int( self.headers['content-length'] )
            #self.sendPage( "text/html", self.rfile.read( length )+'\n' )
            self.processOrder( self.rfile.read( length ) )

    def sendPage( self, contenttype, body ):
        self.send_response( 200 )
        self.send_header( "Access-Control-Allow-Origin", "*" )
        self.send_header( "Content-type", contenttype )
        self.send_header( "Content-length", str(len(body)) )
        self.end_headers()
        self.wfile.write( body )

    def processOrder( self, body ):
        try:
            order = json.loads(body)
        except Exception as e:
            self.send_error(400,"You call that JSON!? <br>\n%s<br>\n You sent (repr'd)<br>\n%r" % (str(e), body))
            return
        try:
            r = redis.StrictRedis(host='localhost', port=6379, db=0)
        except Exception as e:
            self.send_error(500, "Could not connect to redis\n%s\n" % (str(e)))
            return
        # confirm that all the keys we need are present
        try:
            base_size = order['base-size']
            assert base_size in ['hm','1m','2m','3m','4m','5m']
            texture = order['texture']
            assert texture in ['whiterivet']
            secp = order['sections']
            assert type(secp) == list
            assert 0 < len(secp) < 13
            for sec in secp:
                assert type(sec) == dict
                capped = sec['capped']
                assert type(capped) == bool
                profile = sec['profile']
                assert type(profile) == list
                assert len(profile) >= 2
                for vert in profile:
                    assert type(vert) == list
                    assert len(vert) == 2
                    assert type(vert[0]) in [float,int]
                    assert type(vert[1]) in [float,int]
            sections = secp
        except (KeyError, AssertionError) as e:
            self.send_error(400,"JSON message you sent was improperly structured.\n%r\n%r\n" % (e, body))
            self.send_header( "Access-Control-Allow-Origin", "*" )
            return

        # get a new kitid
        kitid = r.incr('kitid-tick')
        time_submitted = time.time()
        
        order['kitid'] = kitid
        order['time-submitted'] = time_submitted

        r.lpush( 'fairing-kit-orders', json.dumps(order) )

        self.sendPage("text/html","Thanks Bro\nkitid=%r\nTime submitted: %0.3f\n" % (kitid, time_submitted))

def httpd(handler_class=MyHandler, server_address = ('', 8008), ):
    srvr = BaseHTTPServer.HTTPServer(server_address, handler_class)
    while True:
        srvr.handle_request() # serve one request

if __name__ == "__main__":
    httpd( )
