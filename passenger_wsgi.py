from cgi import escape, parse_qs
from time import time
from urlparse import urlparse
import re

class Parameters:
  def __init__(self, environ):
    self.parameters = dict()
    self.parameters["HTTP_USER_AGENT"] = environ.get("HTTP_USER_AGENT", "")
    for k, v in parse_qs(environ.get("QUERY_STRING", "")).items():
      self.parameters[k] = v[0]
    self.parameters["REMOTE_ADDR"] = environ.get("REMOTE_ADDR", "")
    self.parameters["REQUEST_URI"] = environ.get("REQUEST_URI", "")

  def get(self, key):
    return self.parameters.get(key, "")

  def empty_request(self):
    return len(self.parameters) <= 2 or not self.get("REQUEST_URI").startswith("/?")

class Response:
  def __init__(self):
    self.content_type = "text/plain"
    self.process = True
    self.response = []
    self.status = "200 OK"

  def append(self, line):
    if len(line) > 0:
      self.response.append(line)

  def set_error(self, message):
    self.process = False
    self.response = [message]
    self.status = "404 Not Found"

  def output(self):
    if len(self.response) == 0:
      return "I|nothing"
    return ["\n".join(self.response)]

class Host:
  def __init__(self, host):
    ip_port = host.split(":")
    if len(ip_port) == 2:
      self.ip = ip_port[0]
      self.port = ip_port[1]
    else:
      self.ip = ""
      self.port = ""

  def ip_port(self):
    return ":".join([self.ip, self.port])

  def is_valid(self):
    if len(self.ip) > 0 and len(self.port) > 0:
      octets = self.ip.split(".")
      if len(octets) == 4:
        for octet in octets:
          try:
            intOctet = int(octet)
            if len(str(intOctet)) == len(octet) and intOctet >= 0 and intOctet <= 255:
              pass
            else:
              return False
          except ValueError:
            return False
      else:
        return False
      try:
        port = self.port
        intPort = int(port)
        if len(str(intPort)) == len(port) and intPort >= 1024 and intPort <= 65535:
          pass
        else:
          return False
      except ValueError:
        return False
    else:
      return False
    return True

class URL:
  def __init__(self, url):
    self.url = url

  def is_valid(self):
    url = urlparse(self.url)
    if len(url) < 6:
      return False
    if url[0] != "http":
      return False
    if len(url[3]) > 0 or len(url[4]) > 0 or len(url[5]) > 0:
      return False
    netloc = url[1]
    if netloc.find("nyud.net") >= 0:
      return False
    banned_domains = ["fascination77.free.fr", "gwc.lcon.ro", "licensed2wed.com", "mortgagemac.com", "5.gc.nonexiste.net", "1.gc.1e400.net", "2.gc.1e400.net", "3.gc.1e400.net", "4.gc.1e400.net", "jayl.de", "gwc.gofoxy.net", "gwc.iblinx.com", "www.gofoxy.net", "www.myfoxy.net", "gwc.divergentlogic.net", "www.delelisten.no", "gwebcache.ns1.net", "dogma.cloud.bishopston.net", "hub.dynoisp.com", "cache1.gwebcache.net", "g2.tjtech.org", "howl.gotdns.org", "gwc2.zapto.org", "www.lo7.wroc.pl", "gwc.nonexiste.net", "1.gc.nonexiste.net", "2.gc.nonexiste.net", "gwc.guufshop.com", "3.gc.nonexiste.net", "4.gc.nonexiste.net"]
    if banned_domains.count(netloc) > 0:
      return False
    netloc_split = netloc.split(":")
    netloc_split_len = len(netloc_split)
    if netloc_split_len > 2:
      return False
    if netloc_split_len > 1:
      try:
        port = netloc_split[1]
        intPort = int(port)
        if len(port) != len(str(intPort)):
          return False
        if intPort < 1 or intPort == 80 or intPort == 443 or intPort > 65535:
          return False
      except ValueError:
        return False
    netloc_dot_split = netloc_split[0].split(".")
    for x in netloc_dot_split:
      if len(x) == 0:
        return False
    if netloc_dot_split[-1].isdigit():
      return False
    if not re.match(r"^[-a-z0-9.]+$", netloc_split[0]):
      return False
    path = url[2]
    if path.endswith(".php/"):
      return False
    if not re.match(r"^/[a-zA-Z0-9/.~_-]*$", path):
      return False
    path_strip = path.rstrip("/")
    path_strip_len = len(path_strip)
    path_len = len(path)
    if path_len != path_strip_len and path_len - 1 != path_strip_len:
      return False
    if path_strip.endswith("index.php"):
      return False
    if self.url.find("?") >= 0:
      return False
    return True

class Cache:
  def __init__(self, parameters):
    self.bans_file = "bans"
    self.urls_file = "urls"
    self.hosts_file = "hosts"
    self.version = "Boa"
    self.max_host_age = 3600
    self.max_url_age = 25200
    self.ban_time = 3300
    self.parameters = parameters
    self.response = Response()

  def get_response(self):
    self.check_user_agent()
    self.check_parameters()
    self.check_net()
    self.check_client()
    self.ping()
    self.update()
    self.get()
    return self.response

  def check_parameters(self):
    if self.response.process and self.parameters.empty_request():
      self.response.content_type = "text/html"
      self.response.append("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\">")
      self.response.append("<META http-equiv=\"Content-Type\" content=\"charset=utf-8\">")
      self.response.append("<STYLE TYPE=\"text/css\">body{background:black;color:#806517;font-family:Tahoma,sans-serif;text-align:center;}</STYLE>")
      self.response.append("<TITLE>")
      self.response.append(self.version)
      self.response.append("</TITLE>")
      self.response.append("<H1>")
      self.response.append(self.version)
      self.response.append("</H1>")
      self.response.process = False

  def check_user_agent(self):
    if self.response.process and self.parameters.get("HTTP_USER_AGENT") == "Shareaza":
      self.response.set_error("")

  def check_net(self):
    if self.response.process and self.parameters.get("net") != "gnutella2":
      self.response.set_error("ERROR: Network Not Supported")

  def check_client(self):
    if self.response.process and self.parameters.get("client") == "":
      self.response.set_error("ERROR: Client must be supplied")

  def update(self):
    if self.response.process and self.parameters.get("update") == "1":
      self.check_banlist()
      self.update_host()
      self.update_url()

  def check_banlist(self):
    data = DataFile(self.bans_file, self.ban_time)
    records = data.load()
    ip = self.parameters.get("REMOTE_ADDR")
    if records.has_key(ip) or not re.match(r"\A(?:[0-9]{1,3}\.){3}[0-9]{1,3}\Z", ip):
      self.response.set_error("ERROR: Client returned too early")
      return
    records[ip] = [ip, str(int(time()))]
    data.save(records)

  def update_host(self):
    if self.response.process:
      ip = self.parameters.get("ip")
      if len(ip) > 0:
        host = Host(ip)
        if host.ip == self.parameters.get("REMOTE_ADDR") and host.is_valid():
          data = DataFile(self.hosts_file, self.max_host_age)
          records = data.load()
          ip_port = host.ip_port()
          records[ip_port] = [ip_port, str(int(time()))]
          data.save(records)
          self.response.append("I|update|OK")
        else:
          self.response.append("I|update|WARNING|Rejected IP")

  def update_url(self):
    if self.response.process:
      url = self.parameters.get("url")
      if len(url) > 0:
        if URL(url).is_valid():
          data = DataFile(self.urls_file, self.max_url_age)
          records = data.load()
          records[url] = [url, str(int(time()))]
          data.save(records)
          self.response.append("I|update|OK")
        else:
          self.response.append("I|update|WARNING|Rejected URL")

  def ping(self):
    if self.response.process and self.parameters.get("ping") == "1":
      self.response.append("|".join(["I|pong", self.version, "gnutella2"]))

  def get(self):
    if self.response.process and self.parameters.get("get") == "1":
      self.response.append(DataFile(self.hosts_file, self.max_host_age).output("H", "HOSTS"))
      self.response.append(DataFile(self.urls_file, self.max_url_age).output("U", "URLS"))

class DataFile:
  def __init__(self, filename, max_age):
    self.filename = filename
    self.max_age = max_age

  def output(self, type, name):
    items = self.load().items()
    if len(items) == 0:
      return "".join(["I|NO-", name])
    return "\n".join("|".join([type, key, str(int(time() - int(record[1])))]) for key, record in items)

  def load(self):
    records = dict()
    try:
      f = open(self.filename, "rb")
      for line in f:
        fields = str(line.decode()).split("|")
        if len(fields) == 2:
          timestamp = fields[1]
          try:
            if time() - int(timestamp) < self.max_age:
              key = fields[0]
              records[key] = [key, timestamp]
          except ValueError:
            pass
    except IOError:
      pass
    else:
      f.close()
    return records

  def save(self, records):
    try:
      f = open(self.filename, "w")
      f.write("\n".join("|".join(value for value in record) for key, record in records.items()))
    except IOError:
      pass
    else:
      f.close()

def application(environ, start_response):
  cache = Cache(Parameters(environ))
  response = cache.get_response()
  start_response(response.status, [('Content-Type', response.content_type)])
  return response.output()
