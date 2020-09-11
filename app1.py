import os
import io
import uuid
import shutil
import sys

import threading
import time
from queue import Empty, Queue

import cv2
from flask import Flask, render_template, flash, send_file, request, jsonify, url_for
from PIL import Image
import numpy as np

from u2net_test import U_2net
#################################################################
app = Flask(__name__, template_folder="templates", static_url_path="/static")
DATA_FOLDER = "data"
# Init Cartoonizer and load its weights


requests_queue = Queue()
BATCH_SIZE = 1
CHECK_INTERVAL = 0.1
##################################################################

# Image Convert function


def convert_bytes_to_image(img_bytes):
    """Convert bytes to numpy array
    Args:
        img_bytes (bytes): Image bytes read from flask.
    Returns:
        [numpy array]: Image numpy array
    """

    pil_image = Image.open(io.BytesIO(img_bytes))
    if pil_image.mode == "RGBA":
        image = Image.new("RGB", pil_image.size, (255, 255, 255))
        image.paste(pil_image, mask=pil_image.split()[3])
    else:
        image = pil_image.convert("RGB")

    image = np.array(image)

    return image


# run


def run(input_file, file_type, f_path):
    try:
        if file_type == "image":
            print(input_file)
            f_name = str(uuid.uuid4())
            img = input_file.read()

            # Original Image Save
            # Run model

            # Save Output Image

            # return result_path

            result_path = output_img_name

            return result_path

    except Exception as e:
        print(e)
        return 500
# Queueing


def handle_requests_by_batch():
    try:
        while True:
            requests_batch = []

            while not (
                len(requests_batch)
                >= BATCH_SIZE  # or
                # (len(requests_batch) > 0 #and time.time() - requests_batch[0]['time'] > BATCH_TIMEOUT)
            ):
                try:
                    requests_batch.append(
                        requests_queue.get(timeout=CHECK_INTERVAL))
                except Empty:
                    continue

            batch_outputs = []

            for request in requests_batch:
                batch_outputs.append(
                    run(request["input"][0], request["input"]
                        [1], request["input"][2])
                )

            for request, output in zip(requests_batch, batch_outputs):
                request["output"] = output

    except Exception as e:
        while not requests_queue.empty():
            requests_queue.get()
        print(e)


# Thread Start
threading.Thread(target=handle_requests_by_batch).start()


@app.route("/")
def main():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        print(requests_queue.qsize())

        if requests_queue.qsize() >= 1:
            return jsonify({"message": "Too Many Requests"}), 429

        input_file = request.files["source"]
        file_type = request.form["file_type"]

        if file_type == "image":
            if input_file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
                return jsonify({"message": "Only support jpeg, jpg or png"}), 400

        input_file.save(secure)
        # mkdir and path setting
        f_id = str(uuid.uuid4())
        f_path = os.path.join(DATA_FOLDER, f_id)
        os.makedirs(f_path, exist_ok=True)

        req = {"input": [input_file, file_type, f_path]}
        print('큐에 들어간다')
        requests_queue.put(req)

        # Thread output response
        while "output" not in req:
            time.sleep(CHECK_INTERVAL)

        if req["output"] == 500:
            return jsonify({"error": "Error! Please upload another file"}), 500

        result_path = req["output"]

        result = send_file(result_path)

        shutil.rmtree(f_path)

        return result

    except Exception as e:
        print(e)

        return jsonify({"message": "Error! Please upload another file"}), 400

    return render_template("hi.html")


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    ne = str(uuid.uuid4())
    print(ne)
    from waitress import serve

    serve(app, host="0.0.0.0", port=80)