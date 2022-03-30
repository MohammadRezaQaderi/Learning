from errno import ENOEXEC
from elasticsearch import Elasticsearch
import json
import base64
from datetime import datetime
import pandas as pd
es = Elasticsearch("http://192.168.231.73:9200/")
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))