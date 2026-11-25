import unittest
from types import SimpleNamespace
from cedar.client import Client
from cedar.transport import Transport
class Smoke(unittest.TestCase):
 def test_fetch_success(self):
  class Adapter:
   def request(self,*args,**kwargs):return SimpleNamespace(status=200,location=None,headers={})
  self.assertEqual(Client(Transport(Adapter())).fetch("https://one.fixture.invalid").status,200)
