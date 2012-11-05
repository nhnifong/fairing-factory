import BaseHTTPServer
import json

class MyHandler( BaseHTTPServer.BaseHTTPRequestHandler ):
    server_version= "FairingFactory/0.2"
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
        self.send_header( "Content-type", contenttype )
        self.send_header( "Content-length", str(len(body)) )
        self.end_headers()
        self.wfile.write( body )

    def processOrder( self, body ):
        try:
            order = json.loads(body)
        except Exception as e:
            self.send_error(400,"You call that JSON!? <br>\n%s<br>\n You sent (repr'd)<br>\n%r" % (str(e), body))
        

        self.sendPage("text/html","Thanks Bro<br>\n")

def httpd(handler_class=MyHandler, server_address = ('', 8008), ):
    srvr = BaseHTTPServer.HTTPServer(server_address, handler_class)
    srvr.handle_request() # serve one request

if __name__ == "__main__":
    httpd( )
