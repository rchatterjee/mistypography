__author__ = "Rahul Chatterjee (rahul@cs.cornell.edu)"

"""
Assuming there is a hashing function that takes a password and
userid and returns true or false. 
"""


# Replace this follwoing funtion with the adequete 
def call_auth_server(uid, pw):
    """This is basically the hook to a authentication server, it calls
    the server with a (uid, pw) tuple and expects a 'True' 'False' (or
    1, 0) types answer.  This function could be very expesive, hence call
    it husbandariliy.
    """
    DB= [('rahulc', 'qwerty'), ('user1', 'Password'), ('user2', 'password'),
         ('abcd@xyz.com', 'abcd123')]
    return (uid, pw) in DB  # PLEASE REPLACE THIS WITH CORRECT CALL




################################################################################
   ############### Actual Typo check and logging code  ####################
################################################################################

from checker import BUILT_IN_CHECKERS
import logging, json

# Set up logger
logging.basicConfig(filename='logs/mistypography.log', level=logging.INFO)
logger = logging.getLogger( __name__ )


CORRECT = 1
INCORRECT = 0
CORRECTABLE = 2

# Set up a UDP server
import SocketServer
import time
timestamp = time.time

def whocanfix(rcv_pwsubmission, correct_pw):
    """
    Logs for each checker whether that can fix this password or not. 
    """
    logformat = "    WHOCANFIX: time={ts}, uid={uid}, user-agent={useragent}, "\
      "correct={isValid}, checkers={checkers!r}"
      
    # TODO - We might want to hash the uid or do something with that before logging
    checkers = []
    rcv_pwsubmission['ts'] = timestamp()
    tpw = rcv_pwsubmission['password']
    isValid = rcv_pwsubmission['isValid']

    if isValid == CORRECTABLE:  # Correctable password submission, check the checkers
        if not correct_pw:
            logger.ERROR("isValid is 2 but correct_pw = '{!r}'".format(correct_pw))
            return
        checkers = [k for k,v in BUILT_IN_CHECKERS.items()
                   if correct_pw in v.get_ball(tpw)]
        if not checkers:
            logger.ERROR("isValid is 2 but no checker could correct"\
                         "this password submission.".format(correct_pw))
            return
            
    else:   # isValid is either 1 or 0, Nothing to do for those.
            # Incorrect submission and cannot be corrected
        pass 

    rcv_pwsubmission['checkers'] = checkers
    rcv_pwsubmission['password'] = ''
    rcv_pwsubmission['uid'] = rcv_pwsubmission.get('uid', 'UID_NOTFOUND')
    rcv_pwsubmission['useragent'] = rcv_pwsubmission.get('useragent', 'UAGENT_NOTFOUND')
    rcv_pwsubmission['isValid'] = rcv_pwsubmission.get('isValid', -2)   # isValid NOT FOUND
    
    logger.info(logformat.format(**rcv_pwsubmission))


class PWTypoUDPHandler(SocketServer.BaseRequestHandler):
    """The checkers take time to initialize, if we restart them every
    time it will super in-efficient. So, this is the server will will
    accept json serializable query of user's password submissions, (see below), 
    and log accordingly using whocanfix function.
    """

    def isCorrectable(self, uid, pw):
        """Apply all the correctors and see if anyone of them can fix the password.
        returns the correct password if there is such corrector, None otherwise.
        
        """
        ## TODO - we may want to order the fixed password in the order
        ## of the effectiveness of the corrector.
        B = list(BUILT_IN_CHECKERS['ChkAllTop5'].get_ball(pw))  # ChkAllTop5 contains all correctors

        # Following call can be parallelized if the auth server
        # supports
        for fixed_pw in B:
            if call_auth_server(uid, fixed_pw)==1: # correctable returns the correct password
                return fixed_pw

        return None     # not correctable, returns None


    def handle(self):
        """
        Expects the input to be in the following format:
           {
              'uid': <some-uid>,   # unique for each user
              'password':  <the entered password>
              'isValid': 0 (or 1, -1), # if this password has already been validated, 
                                       # 0 for wrong, 1 for right, -1 not checked yet.
              'useragent': <user agent string>
           }

        """
        data = self.request[0].strip()
        socket = self.request[1]
        # print "{} wrote:".format(self.client_address[0])        
        rcv_pwsubmission = json.loads(data)

        ## TODO - Probably we should remove this in production
        
        logger.info('    Received from address={!r}, data={!r} at time={}'\
                    .format(self.client_address, rcv_pwsubmission, timestamp()))
        uid, tpw = rcv_pwsubmission.get('uid', ''), rcv_pwsubmission.get('password', '')
        isValid = rcv_pwsubmission.get('isValid', -1)

        if not tpw or not uid:
            return
        if isValid==-1:
            isValid = call_auth_server(uid, tpw)
            rcv_pwsubmission['isValid'] = isValid

        if isValid==CORRECT:
            correct_pw = tpw
        else:
            correct_pw = self.isCorrectable(uid, tpw)
            if correct_pw:
                rcv_pwsubmission['isValid'] = CORRECTABLE      # Correctable password

        whocanfix(rcv_pwsubmission, correct_pw)
        socket.sendto(correct_pw, self.client_address)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = SocketServer.UDPServer((HOST, PORT), PWTypoUDPHandler)
    server.serve_forever()
