import socket
import json

sample_json = {
    "name": "G. Castle Defense",
    "group": "Codeforces - Educational Codeforces Round 40 (Rated for Div. 2)",
    "url": "https://codeforces.com/problemset/problem/954/G",
    "interactive": False,
    "memoryLimit": 256,
    "timeLimit": 1500,
    "tests": [
        {
            "input": "5 0 6\n5 4 3 4 9\n",
            "output": "5\n"
        }
    ],
    "testType": "single",
    "input": {"type": "stdin"},
    "output": {"type": "stdout"},
    "languages": {
        "java": {
            "mainClass": "Main",
            "taskClass": "GCastleDefense"
        }
    },
    "batch": {
        "id": "123e67c8-03c6-44a4-a3f9-5918533f9fb2",
        "size": 1
    }
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("127.0.0.1", 27121))
    s.sendall(json.dumps(sample_json).encode())
    print("✅ Sent sample JSON")

