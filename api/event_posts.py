from http.server import BaseHTTPRequestHandler
from pymongo import MongoClient
import json
from bson import json_util
from urllib.parse import parse_qs, urlparse
import os
from dotenv import load_dotenv

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录路径
root_dir = os.path.dirname(current_dir)
# 加载根目录下的 .env 文件
load_dotenv(os.path.join(root_dir, '.env'))

# 数据库连接
def connect_to_db():
    client = MongoClient(os.getenv('MONGO_URI'))
    return client['weibo']['weibo']

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 修改路径解析逻辑
            path = self.path.split('?')[0]  # 移除查询参数
            event_id = int(path.split('/')[-1])  # 获取最后一个路径段
            
            if not event_id:
                raise ValueError("Missing event id")
                
            collection = connect_to_db()
            pipeline = [
                {
                    "$match": {
                        "summary_embedding_cluster_label": event_id
                    }
                },
                {"$sort": {"created_at": -1}},
                {
                    "$project": {
                        "id": 1,
                        "text": 1,
                        "screen_name": 1,
                        "attitudes_count": 1,
                        "comments_count": 1,
                        "reposts_count": 1,
                        "created_at": 1,
                        "response": {"$ifNull": ["$response", 0]}
                    }
                }
            ]

            posts = list(collection.aggregate(pipeline))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-store, must-revalidate')
            self.end_headers()
            
            self.wfile.write(json_util.dumps({"posts": posts}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_msg = {"error": str(e)}
            self.wfile.write(json.dumps(error_msg).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.end_headers() 