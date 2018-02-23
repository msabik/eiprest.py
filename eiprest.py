#!/usr/bin/python
'''
###################################################################
 Simple Python implementation for SOLIDserver REST client
 Version: 1.0.0

 Examples:
 - using simple parameter format
   eiprest.py --server 10.0.99.99 dns_server_info dns_id=3
 - using json parameter format
   eiprest.py --server 10.0.99.99 dns_server_info '{"dns_id":3}'
 - using as python module in another script
   from eiprest import EipRest
   rest = EipRest(host='10.0.99.99', user='ipmadmin', password='admin', debug=True)
   params = {'dns_id': 3}
   rest.query('GET', 'dns_server_info',  params)
   rest.show_result()

 Run eiprest.py -h to see more options.
####################################################################
'''

import sys
import argparse
import base64
import urllib
import json
import requests
from pprint import pprint
# For python2 compatibility
try:
  # python 3
  from urllib.parse import quote_plus
except ImportError:
  # python 2
  from urllib import quote_plus

class EipRestException(RuntimeError):
  def __init__(self, arg):
    self.args = arg

class EipRest(object):

  @staticmethod
  def param2str(params):
    '''convert params in format "key1=val1&key2=val2"'''
    
    if params is None:
      return ''
    elif type(params) is dict:
      tmp_params = ["{}={}".format(k, quote_plus(str(params[k]))) for k in params.keys()]
      return '&'.join(tmp_params)
    elif type(params) is str:
      if params.startswith("{"): # params in json format
        try:
          d = json.loads(params)
          tmp_params = ["{}={}".format(k, quote_plus(str(params[k]))) for k in d.keys()]
          return '&'.join(tmp_params)
        except:
          raise EipRestException("Bas parameter format: {}".format(params))
      else:
        return params
    else:
      raise EipRestException("Bas parameter type: {}".format(type(params)))

  @staticmethod
  def param2dict(params):
    '''convert string format "key1=val1&key2=val2" or json format to dict'''
    
    if params is None or type(params) is dict:
      return params

    if type(params) is str:
      if params.startswith("{"): # params in json format
        try:
          return json.loads(params)
        except:
          raise EipRestException("Bad parameter format: {}".format(params))
      else:
        dict_params = {}
        for param in params.split('&'):
          tmp = param.split('=', 1)
          if len(tmp) == 2:
            if tmp[0] in ('SELECT','WHERE','GROUPBY','ORDERBY','OPT_SELECT'):
              dict_params[tmp[0]] = urllib.unquote_plus(tmp[1])
            else:
              dict_params[tmp[0]] = tmp[1]
          else:
            raise EipRestException("Bas parameter format: {}".format(params))
        return dict_params
    else:
      raise EipRestException("Bas parameter type: {}".format(type(params)))
            
          
  def __init__(self, host, user, password, debug=False):
    self.debug = debug
    self.host = host
    self.user = user
    print("EipRest({}, {})".format(host,user))
    self.password = password
    self.prefix = 'https://{}/rest/'.format(host)
    # ipmadmin:aXBtYWRtaW4=
    # admin:YWRtaW4=
    if sys.version_info[0] == 3:
      self.headers = {'X-IPM-Username': base64.b64encode(user.encode()),
                      'X-IPM-Password': base64.b64encode(password.encode()),
                      'content-type': 'application/json'}
    else:
      self.headers = {'X-IPM-Username': base64.standard_b64encode(user),
                      'X-IPM-Password': base64.standard_b64encode(password),
                      'content-type': 'application/json'}
    self.last_url = ''
    self.resp = None

  def show_result(self):
    if self.resp:
      print("=========================")
      print("Response:")
      print("=========================")
      print("status code: {}".format(self.resp.status_code))
      try:
        if sys.version_info[0] == 3:
          data = json.loads(self.resp.content.decode())
        else:
          data = json.loads(self.resp.content)
      except ValueError:
        #json decoding failed
        data = None
      if data is None:
        print("content size: 0kB")
        print("nb objects: 0")
      else:
        print("content size: %dkB" % (len(self.resp.content)/1024))
        print("nb objects: %d" % len(data))
        if self.debug:
          if type(data) is list:
            n = 1
            for d in data:
              print("--------------------------------------------")
              #print("object {}".format(n))
              #print("----------")
              for k in d:
                print("{} => {}".format(k, d[k]))
              n += 1
          elif type(data) is dict:
            print("--------------------------------------------")
            for d in data:
              print("{} => {}".format(d, data[d]))
            print("----------")

  def query(self, method, service, params=None, payload=None):

    method = method.upper()
    url = self.prefix + service
    if method == 'GET':
      self.last_url = "{} {} {}".format(method, service, self.param2str(params)).strip()
      self.resp = requests.request(method, url,
                                   headers=self.headers,
                                   params=params,
                                   verify=False)
    elif method == 'OPTIONS':
      self.last_url = "{} {}".format(method, service)
      self.resp = requests.request(method, url, headers=self.headers, verify=False)
    else:
      self.last_url = "{} {} {}".format(method, service, self.param2str(params)).strip()
      if payload:
        self.last_url += " " + payload
      self.resp = requests.request(method, url,
                                   headers=self.headers,
                                   params=params,
                                   data=payload,
                                   verify=False)
    #print(self.resp)


  def rpc(self, method, service, params=None, payload=None):
    method = method.upper()
    self.last_url = "{} {} {}".format(method, service, self.param2str(params)).strip()
    if payload:
      self.url += " " + payload
    self.resp = requests.request(method,
                                 "https://{}/rpc/{}".format(self.host, service),
                                 headers=self.headers,
                                 params=params,
                                 verify=False)
    #print(self.resp)

    

######################################################################
# Run as top-level script
######################################################################

if __name__ == "__main__":

    from pprint import pprint
  
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='enable debug mode', action='store_true')
    parser.add_argument('-s', '--server', help='Solidserver hostname or ip', required=True)
    parser.add_argument('-u', '--user', help='user name', default='ipmadmin')
    parser.add_argument('-p', '--password', help='user password', default='admin')
    parser.add_argument('-m', '--method', help='HTTP method', default='GET', choices=['GET','POST','PUT','DELETE','OPTIONS'])
    parser.add_argument('-r', '--rpc', help='use RPC API instead of REST API', action='store_true')
    parser.add_argument('--where', help='WHERE parameter of the service')
    parser.add_argument('service', help='service to run')
    parser.add_argument('parameters', help='paramters of the service', nargs='?')
    
    args = parser.parse_args()

    rest = EipRest(args.server, args.user, args.password, args.debug)
    param = rest.param2dict(args.parameters)
    if param is None:
        param = {}
    if args.where:
        param.update({'WHERE': args.where})
            
    print("===========================")
    if args.rpc:
        print("RPC: {} {} {}".format(args.method, args.service, json.dumps(param)))
    else:
        print("REST: {} {} {}".format(args.method, args.service, json.dumps(param)))

    if args.rpc:
        rest.rpc(args.method, args.service, param)
    else:        
        rest.query(args.method, args.service, param)
  
    rest.show_result()
