import os
import time
import subprocess
import signal

from beach.beach_api import Beach
from beach.utils import *

h_hostmanager = None
beach = None
curFileDir = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ) )



def test_create_single_node_cluster():
    global h_hostmanager
    h_hostmanager = subprocess.Popen( [ 'python',
                                        '-m',
                                        'beach.hostmanager',
                                        os.path.join( curFileDir, 'simple.yaml' ) ] )

    time.sleep( 2 )

    assert( h_hostmanager.returncode is None )


def test_beach_connection():
    import yaml
    from beach.utils import _getIpv4ForIface
    global beach

    beach = Beach( os.path.join( curFileDir, 'simple.yaml' ),
                   realm = 'global' )
    time.sleep( 1 )
    assert( 1 == beach.getNodeCount() )


def test_actor_creation():
    global beach

    a1 = beach.addActor( 'Ping', 'pingers' )
    assert( isMessageSuccess( a1 ) )

    a2 = beach.addActor( 'Pong', 'pongers' )
    assert( isMessageSuccess( a2 ) )

    time.sleep( 2 )

    d = beach.getDirectory()
    assert( 1 == len( d.get( 'realms', {} ).get( 'global', {} ).get( 'pingers', {} ) ) )
    assert( 1 == len( d.get( 'realms', {} ).get( 'global', {} ).get( 'pongers', {} ) ) )

def test_isolated_actor_creation():
    global beach

    a1 = beach.addActor( 'Ping', 'pingers', isIsolated = True )
    assert( isMessageSuccess( a1 ) )

    time.sleep( 2 )

    d = beach.getDirectory()
    assert( 2 == len( d.get( 'realms', {} ).get( 'global', {} ).get( 'pingers', {} ) ) )
    assert( 1 == len( d.get( 'realms', {} ).get( 'global', {} ).get( 'pongers', {} ) ) )

def test_virtual_handles():
    global beach

    vHandle = beach.getActorHandle( 'pongers' )
    resp = vHandle.request( 'ping', data = { 'source' : 'outside' }, timeout = 10 )
    assert( resp.isSuccess and 'time' in resp.data )

def test_prefix_virtual_handles():
    global beach

    vHandles = beach.getActorHandle( 'p' )
    gevent.sleep( 1 )
    assert( 3 == vHandles.getNumAvailable() )
    assert( vHandles.isAvailable() is True )

    vHandles = beach.getActorHandle( 'p/' )
    gevent.sleep( 1 )
    assert( 0 == vHandles.getNumAvailable() )
    assert( vHandles.isAvailable() is False )

def test_flushing_single_node_cluster():
    f = beach.flush()
    assert( f )

    d = beach.getDirectory()
    assert( 0 == len( d.get( 'realms', {} ).get( 'global', {} ).get( 'pingers', {} ) ) )
    assert( 0 == len( d.get( 'realms', {} ).get( 'global', {} ).get( 'pongers', {} ) ) )



def test_trust():
    global beach

    a1 = beach.addActor( 'Pong', 'pongers/trust', trustedIdents = [ 'abc' ] )
    assert( isMessageSuccess( a1 ) )

    a2 = beach.addActor( 'Pong', 'pongers/notrust', trustedIdents = [ 'def' ] )
    assert( isMessageSuccess( a2 ) )

    vHandle = beach.getActorHandle( 'pongers/trust', ident = 'abc' )
    resp = vHandle.request( 'ping', data = { 'source' : 'outside' }, timeout = 10 )
    assert( resp.isSuccess and 'time' in resp.data )

    vHandle = beach.getActorHandle( 'pongers/notrust', ident = 'abc' )
    resp = vHandle.request( 'ping', data = { 'source' : 'outside' }, timeout = 10 )
    assert( not resp.isSuccess and resp.error == 'unauthorized' )

    vHandle = beach.getActorHandle( 'pongers/notrust', ident = 'def' )
    resp = vHandle.request( 'ping', data = { 'source' : 'outside' }, timeout = 10 )
    assert( resp.isSuccess and 'time' in resp.data )


def test_terminate_single_node_cluster():
    global h_hostmanager
    global beach
    beach.close()
    h_hostmanager.send_signal( signal.SIGQUIT )

    assert( 0 == h_hostmanager.wait() )