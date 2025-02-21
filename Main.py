from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)
active_processes = {}

def post_comment(post_id, comment, token, hater_name):
    """Posts a comment on a Facebook post."""
    url = f"https://graph.facebook.com/{post_id}/comments"
    message = f"[{hater_name}] {comment}" if hater_name else comment
    payload = {"message": message, "access_token": token}
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print(f"✅ Comment Sent: {comment} on Post ID: {post_id}")
    else:
        print(f"❌ Failed on Post ID {post_id}: {response.json()}")

def start_commenting(task_id, post_id, comments, speed, token, hater_name):
    """Continuously posts comments on a post until stopped."""
    while active_processes.get(task_id, False):
        comment = comments.pop(0)
        post_comment(post_id, comment, token, hater_name)
        comments.append(comment)
        time.sleep(speed)

@app.route('/api/start', methods=['POST'])
def start():
    """Starts an auto-commenting process."""
    data = request.json
    task_id = data["task_id"]
    post_id = data["post_id"]
    resume_post_id = data.get("resume_post_id")
    comments = data["comments"]
    speed = data["speed"]
    token = data["token"]
    hater_name = data.get("hater_name")

    if not all([task_id, post_id, comments, speed, token]):
        return jsonify({"error": "Invalid data"}), 400

    # Start main post commenting
    active_processes[task_id] = True
    thread = threading.Thread(target=start_commenting, args=(task_id, post_id, comments, speed, token, hater_name))
    thread.start()
    
    # Start resume post commenting if provided
    if resume_post_id:
        resume_task_id = f"{task_id}_resume"
        active_processes[resume_task_id] = True
        thread = threading.Thread(target=start_commenting, args=(resume_task_id, resume_post_id, comments, speed, token, hater_name))
        thread.start()

    return jsonify({"message": "Auto-commenting started on both posts!" if resume_post_id else "Auto-commenting started!"})

@app.route('/api/active', methods=['GET'])
def active_loader():
    """Returns a list of active loaders."""
    return jsonify({"active_loaders": list(active_processes.keys())})

@app.route('/api/stop', methods=['POST'])
def stop():
    """Stops a specific auto-commenting process."""
    data = request.json
    task_id = data.get("task_id")

    if not task_id:
        return jsonify({"error": "Task ID required"}), 400

    if task_id in active_processes:
        del active_processes[task_id]
        return jsonify({"message": f"Auto-commenting stopped for Task ID: {task_id}"})
    
    return jsonify({"error": f"No active process found for Task ID: {task_id}"}), 400

@app.route('/api/stop-all', methods=['POST'])
def stop_all():
    """Stops all running auto-commenting processes."""
    active_processes.clear()
    return jsonify({"message": "All auto-commenting processes stopped!"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
