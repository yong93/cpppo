from __future__ import absolute_import
from __future__ import print_function

import logging
import multiprocessing
import os
import random
import socket
import sys
import threading
import time
import traceback

try:
    from reprlib import repr as repr
except ImportError:
    from repr import repr as repr

if __name__ == "__main__" and __package__ is None:
    # Allow relative imports when executing within package directory, for
    # running tests directly
    sys.path.insert( 0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cpppo
from   cpppo.server import ( enip, network )

logging.basicConfig( **cpppo.log_cfg )
log				= logging.getLogger( "enip.tst" )

def test_octets():
    """Scans raw octets"""
    data			= cpppo.dotdict()
    source			= cpppo.chainable( b'abc123' )
    name			= "five"
    with enip.octets( name, repeat=5, context=name ) as machine:
        for i,(m,s) in enumerate( machine.run( source=source, path='octets', data=data )):
            log.info( "%s #%3d -> %10.10s; next byte %3d: %-10.10r: %r", m.name_centered(),
                      i, s, source.sent, source.peek(), data )
        assert i == 4
    assert source.peek() == b'3'[0]

    assert data.octets.five_input.tostring() == b'abc12'


def test_octets_struct():
    """Parses a specified struct format from scanned octets"""

    data			= cpppo.dotdict()
    source			= cpppo.chainable( b'abc123' )
    name			= 'ushort'
    format			= '<H'
    with enip.octets_struct( name, format=format, context=name ) as machine:
        for i,(m,s) in enumerate( machine.run( source=source, path='octets_struct', data=data )):
            log.info( "%s #%3d -> %10.10s; next byte %3d: %-10.10r: %r", m.name_centered(),
                      i, s, source.sent, source.peek(), data )
        assert i == 1
    assert source.peek() == b'c'[0]

    assert data.octets_struct.ushort_input.tostring() == b'ab'
    assert data.octets_struct.ushort == 25185

def test_enip():
    # pkt4
    # "4","0.000863000","192.168.222.128","10.220.104.180","ENIP","82","Register Session (Req)"
    rss_004_request 		= bytes(bytearray([
        # Register Session
                                            0x65, 0x00, #/* 9.....e. */
        0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, #/* ........ */
        0x00, 0x00                                      #/* .. */
    ]))
    # pkt6
    # "6","0.152924000","10.220.104.180","192.168.222.128","ENIP","82","Register Session (Rsp)"
    rss_004_reply 		= bytes(bytearray([
                                            0x65, 0x00, #/* ......e. */
        0x04, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, #/* ........ */
        0x00, 0x00                                      #/* .. */
    ]))
    # pkt8
    # "8","0.153249000","192.168.222.128","10.220.104.180","CIP","100","Get Attribute All"
    gaa_008_request 		= bytes(bytearray([
                                            0x6f, 0x00, #/* 9.w...o. */
        0x16, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x06, 0x00, 0x01, 0x02, #/* ........ */
        0x20, 0x66, 0x24, 0x01                          #/*  f$. */
    ]))
    # pkt10
    # "10","0.247332000","10.220.104.180","192.168.222.128","CIP","116","Success"
    gaa_008_reply 		= bytes(bytearray([
                                            0x6f, 0x00, #/* ..T...o. */
        0x26, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* &....... */
        0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x16, 0x00, 0x81, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x2d, 0x00, 0x01, 0x00, 0x01, 0x01, 0xb1, 0x2a, #/* -......* */
        0x1b, 0x00, 0x0a, 0x00                          #/* .... */
    ]))
    # pkt11
    # "11","0.247477000","192.168.222.128","10.220.104.180","CIP CM","114","Unconnected Send: Get Attribute All"
    gaa_011_request	 		= bytes(bytearray([
                                            0x6f, 0x00, #/* 9.....o. */
        0x24, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* $....... */
        0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x14, 0x00, 0x52, 0x02, #/* ......R. */
        0x20, 0x06, 0x24, 0x01, 0x01, 0xfa, 0x06, 0x00, #/*  .$..... */
        0x01, 0x02, 0x20, 0x01, 0x24, 0x01, 0x01, 0x00, #/* .. .$... */
        0x01, 0x00                                      #/* .. */
    ]))
    # pkt13
    # "13","0.336669000","10.220.104.180","192.168.222.128","CIP","133","Success"
    gaa_011_reply	 		= bytes(bytearray([
                                            0x6f, 0x00, #/* ..dD..o. */
        0x37, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* 7....... */
        0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x27, 0x00, 0x81, 0x00, #/* ....'... */
        0x00, 0x00, 0x01, 0x00, 0x0e, 0x00, 0x36, 0x00, #/* ......6. */
        0x14, 0x0b, 0x60, 0x31, 0x1a, 0x06, 0x6c, 0x00, #/* ..`1..l. */
        0x14, 0x31, 0x37, 0x35, 0x36, 0x2d, 0x4c, 0x36, #/* .1756-L6 */
        0x31, 0x2f, 0x42, 0x20, 0x4c, 0x4f, 0x47, 0x49, #/* 1/B LOGI */
        0x58, 0x35, 0x35, 0x36, 0x31                    #/* X5561 */
        ]))
    # pkt14
    # "14","0.337357000","192.168.222.128","10.220.104.180","CIP CM","124","Unconnected Send: Unknown Service (0x52)"
    unk_014_request 		= bytes(bytearray([
                                            0x6f, 0x00, #/* 9.#...o. */
        0x2e, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x1e, 0x00, 0x52, 0x02, #/* ......R. */
        0x20, 0x06, 0x24, 0x01, 0x05, 0x9d, 0x10, 0x00, #/*  .$..... */
        0x52, 0x04, 0x91, 0x05, 0x53, 0x43, 0x41, 0x44, #/* R...SCAD */
        0x41, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, #/* A....... */
        0x01, 0x00, 0x01, 0x00                          #/* .... */  
    ]))
    # pkt16
    # "16","0.423402000","10.220.104.180","192.168.222.128","CIP","102","Success"
    unk_014_reply 		= bytes(bytearray([
                                            0x6f, 0x00, #/* ..7...o. */
        0x18, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x08, 0x00, 0xd2, 0x00, #/* ........ */
        0x00, 0x00, 0xc3, 0x00, 0x27, 0x80              #/* ....'. */
    ]))
    # pkt17
    # "17","0.423597000","192.168.222.128","10.220.104.180","CIP CM","124","Unconnected Send: Unknown Service (0x52)"
    unk_017_request 		= bytes(bytearray([
                                            0x6f, 0x00, #/* 9.....o. */
        0x2e, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x1e, 0x00, 0x52, 0x02, #/* ......R. */
        0x20, 0x06, 0x24, 0x01, 0x05, 0x9d, 0x10, 0x00, #/*  .$..... */
        0x52, 0x04, 0x91, 0x05, 0x53, 0x43, 0x41, 0x44, #/* R...SCAD */
        0x41, 0x00, 0x14, 0x00, 0x02, 0x00, 0x00, 0x00, #/* A....... */
        0x01, 0x00, 0x01, 0x00                          #/* .... */
    ]))
    # pkt19
    #"19","0.515458000","10.220.104.180","192.168.222.128","CIP","138","Success"
    unk_017_reply		= bytes(bytearray([
                                            0x6f, 0x00, #/* ..jz..o. */
        0x3c, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* <....... */
        0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x2c, 0x00, 0xd2, 0x00, #/* ....,... */
        0x00, 0x00, 0xc3, 0x00, 0x4c, 0x10, 0x08, 0x00, #/* ....L... */
        0x03, 0x00, 0x02, 0x00, 0x02, 0x00, 0x02, 0x00, #/* ........ */
        0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, 0xe6, 0x42, #/* .......B */
        0x07, 0x00, 0xc8, 0x40, 0xc8, 0x40, 0x00, 0x00, #/* ...@.@.. */
        0xe4, 0x00, 0x00, 0x00, 0x64, 0x00, 0xb2, 0x02, #/* ....d... */
        0xc8, 0x40                                      #/* .@ */
    ]))
    # pkt20
    # "20","0.515830000","192.168.222.128","10.220.104.180","CIP CM","130","Unconnected Send: Unknown Service (0x53)"
    unk_020_request 		= bytes(bytearray([
                                            0x6f, 0x00, #/* 9.X...o. */
        0x34, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* 4....... */
        0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x24, 0x00, 0x52, 0x02, #/* ....$.R. */
        0x20, 0x06, 0x24, 0x01, 0x05, 0x9d, 0x16, 0x00, #/*  .$..... */
        0x53, 0x05, 0x91, 0x05, 0x53, 0x43, 0x41, 0x44, #/* S...SCAD */
        0x41, 0x00, 0x28, 0x0c, 0xc3, 0x00, 0x01, 0x00, #/* A.(..... */
        0x00, 0x00, 0x00, 0x00, 0xc9, 0x40, 0x01, 0x00, #/* .....@.. */
        0x01, 0x00                                      #/* .. */
    ]))
    # pkt22
    # "22","0.602090000","10.220.104.180","192.168.222.128","CIP","98","Success"
    unk_020_reply 		= bytes(bytearray([
                                            0x6f, 0x00, #/* ..&...o. */
        0x14, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x04, 0x00, 0xd3, 0x00, #/* ........ */
        0x00, 0x00                                      #/* .. */
    ]))
    # pkt23
    # "23","0.602331000","192.168.222.128","10.220.104.180","CIP CM","126","Unconnected Send: Unknown Service (0x52)"
    unk_023_request 		= bytes(bytearray([
                                            0x6f, 0x00, #/* 9..x..o. */
        0x30, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* 0....... */
        0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x20, 0x00, 0x52, 0x02, #/* .... .R. */
        0x20, 0x06, 0x24, 0x01, 0x05, 0x9d, 0x12, 0x00, #/*  .$..... */
        0x52, 0x05, 0x91, 0x05, 0x53, 0x43, 0x41, 0x44, #/* R...SCAD */
        0x41, 0x00, 0x28, 0x0c, 0x01, 0x00, 0x00, 0x00, #/* A.(..... */
        0x00, 0x00, 0x01, 0x00, 0x01, 0x00              #/* ...... */
    ]))
    # pkt 25
    # "25","0.687210000","10.220.104.180","192.168.222.128","CIP","102","Success"
    unk_023_reply 		= bytes(bytearray([
                                            0x6f, 0x00, #/* ...c..o. */
        0x18, 0x00, 0x01, 0x1e, 0x02, 0x11, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, #/* ........ */
        0x00, 0x00, 0xb2, 0x00, 0x08, 0x00, 0xd2, 0x00, #/* ........ */
        0x00, 0x00, 0xc3, 0x00, 0xc8, 0x40              #/* .....@ */
    ]))

   
    for pkt,tst in [
            ( rss_004_request, { 'enip.header.command': 0x0065 }),
            ( rss_004_reply,	{} ),
            ( gaa_008_request,	{} ),
            ( gaa_008_reply,	{} ),
            ( gaa_011_request,	{} ),
            ( gaa_011_reply,	{} ),
            ( unk_014_request,	{} ),
            ( unk_014_reply,	{} ),
            ( unk_017_request,	{} ),
            ( unk_017_reply,	{} ),
            ( unk_020_request,	{} ),
            ( unk_020_reply,	{} ),
            ( unk_023_request,	{} ),
            ( unk_023_reply,	{} ), ]:
        data			= cpppo.dotdict()
        source			= cpppo.chainable( pkt )
        name			= 'header'
        with enip.enip_header( name, context=name ) as machine:
            for i,(m,s) in enumerate( machine.run( source=source, path='enip', data=data )):
                log.info( "%s #%3d -> %10.10s; next byte %3d: %-10.10r: %r", m.name_centered(),
                          i, s, source.sent, source.peek(), data )
            assert i == 18
        log.warning( "Data: %r", data )
        assert source.peek() == b'\x00'[0]
   
        for k,v in tst.items():
            assert data[k] == v