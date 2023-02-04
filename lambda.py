import os
import logging
import base64
import zlib
import pprint
import json
import datetime
import re

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

HOOK_URL = os.environ['HOOK_URL']

def lambda_handler(event, context):
    # logger.info('## ENVIRONMENT VARIABLES')
    # logger.info(os.environ)
    # logger.info('## EVENT')
    # logger.info(event)
    
    now = datetime.datetime.now()
    now = now.strftime("%Y/%m/%d, %H:%M:%S")
    
    data = event["awslogs"]["data"]
    
    json_str = zlib.decompress(base64.b64decode(data), 16 + zlib.MAX_WBITS).decode('utf-8')
    
    json_str = json.loads(json_str)
    
    instance = json_str["logStream"]
    print(instance)
    message = json_str["logEvents"][0]["message"]
    print(message)
    print("")
    print("")
    
    sql = message.split("SET timestamp=")[1]
    message = message.split("SET timestamp=")[0]
    
    # 2022-07-24T04:40:29.096908Z
    p = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})')
    m = p.search(message)
    
    now_str = m.group()
    now_dtm = datetime.datetime.strptime(now_str, "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(hours=9)
    print("now : ", now_dtm)
    
    l_messages = message.split(":")
    
    
    
    l_messages = l_messages[4:]
    
    l_messages = [ "".join(m.split(" ")[:-1]) for m in l_messages ]
    
    # ['admin[admin]@[172.10.3.210]', '256398#', '5.000289', '0.000000', '1', '']
    
    m_user = l_messages[0]
    m_thread = l_messages[1]
    m_query_time = l_messages[2]
    m_lock_time = l_messages[3]
    m_rows = l_messages[4]
    m_sql = sql
    
    # print(json.dumps(json_str, indent=4, sort_keys=True))
    
    color = "#30db3f"
    
    slack_message = {
      "attachments": [
        {
    	        "mrkdwn_in": ["text"],
                "color": "#36a64f",
                "pretext": now + "\nRDS Slow Log (over 3 seconds)",
                "title": "Instance",
                "text": "`"+instance+"`",
                "fields": [
                    {
                        "title": "User",
                        "value": m_user,
                        "short": False
                    },
                    {
                        "title": "Thread ID",
                        "value": (m_thread.replace("\n","")).replace("#",""),
                        "short": False
                    },
                    {
                        "title": "Elapsed Time(s)",
                        "value": m_query_time,
                        "short": False
                    },
                    {
                        "title": "Lock time(s)",
                        "value": m_lock_time,
                        "short": False
                    },
                    {
                        "title": "Rows",
                        "value": m_rows,
                        "short": False
                    },
                    {
                        "title": "SQL",
                        "value": "".join(m_sql.split(";")[1:]),
                        "short": False
                    }
                ]
            }
        ]
    }

    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted")
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)