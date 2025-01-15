from http.server import BaseHTTPRequestHandler
from pymongo import MongoClient

import json
from bson import json_util

def connect_to_db():
    client = MongoClient('你MongoDB的连接URI')
    return client['weibo']['weibo']

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            collection = connect_to_db()
            pipeline = [
                {
                    "$match": {
                        "event_id": {"$exists": True},
                        "event_title": {"$exists": True},
                        "text": {"$exists": True},
                        "summary_embedding_cluster_label": {"$exists": True, "$ne": -1}
                    }
                },
                {"$sort": {"created_at": -1}},
                {
                    "$group": {
                        "_id": "$event_id",
                        "event_title": {"$first": "$event_title"},
                        "posts": {
                            "$push": {
                                "id": "$id",
                                "text": "$text",
                                "screen_name": "$screen_name",
                                "attitudes_count": "$attitudes_count",
                                "comments_count": "$comments_count",
                                "reposts_count": "$reposts_count",
                                "created_at": "$created_at",
                                "response": {"$ifNull": ["$response", 0]}
                            }
                        }
                    }
                },
                {
                    "$match": {
                        "$expr": {"$gte": [{"$size": "$posts"}, 6]}
                    }
                }
            ]
            
            documents = list(collection.aggregate(pipeline))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {"events": documents}
            self.wfile.write(json_util.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())