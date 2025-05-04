# inference_upload.py – offline folder *or* live camera, full debug, never hangs
# Flow:
#  1. POST {"object_key": key}  → presigned URL (upload_url)
#  2. POST binary JPG           → upload_url
#  3. POST metadata JSON        → /presigned  (image_url = upload_url)
# Features:
#  • Choose between --source <folder>  or --camera <device> (mutually-exclusive).
#  • Robust _request(): dumps status/headers/body on any non-2xx, retries on 429.
#  • All failures are logged but never abort the main loop.
#  • Always saves the same metadata JSON locally.

import argparse
import os
import cv2
import json
import random
import datetime
import time
import numpy as np
import requests
from typing import Optional
from requests import Response
from urllib.parse import urlparse
import traceback
from ultralytics import YOLO

API_POST_URL = "https://d3hi3054wpq3c0.cloudfront.net/presigned"
API_KEY      = "icam-540"
MAX_RETRIES  = 5
BASE_BACKOFF = 2   # seconds
TIMEOUT      = 10  # seconds
DEBUG_LEN    = 300 # body chars to show

# -----------------------------------------------------------
# Debug helpers
# -----------------------------------------------------------

def _dump(resp: Response, ctx: str):
    print(f"[DEBUG] {ctx}: status={resp.status_code}")
    print("[DEBUG] headers:", dict(resp.headers))
    try:
        body = resp.text
        print(f"[DEBUG] body: {body[:DEBUG_LEN]}{'…' if len(body)>DEBUG_LEN else ''}")
    except Exception as e:
        print("[DEBUG] body decode error:", e)

# -----------------------------------------------------------
# Resilient requester
# -----------------------------------------------------------

def _request(method: str, url: str, *, headers: dict, data=None, json_body=None) -> Optional[Response]:
    backoff = BASE_BACKOFF
    for attempt in range(1, MAX_RETRIES+1):
        try:
            resp = requests.request(method, url, headers=headers, data=data, json=json_body, timeout=TIMEOUT)
            if resp.status_code < 300:
                return resp
            if resp.status_code == 429:
                retry = int(resp.headers.get("Retry-After", 0)) or backoff
                print(f"[WARN] 429 {url} -> sleep {retry}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(retry)
                backoff *= 2
                continue
            _dump(resp, f"{method} {url}")
        except requests.RequestException as e:
            print(f"[ERROR] {method} {url}: {e} (attempt {attempt}/{MAX_RETRIES})")
        time.sleep(backoff)
        backoff *= 2
    print(f"[ERROR] exceeded retries for {url}")
    return None

# -----------------------------------------------------------
# Upload helpers
# -----------------------------------------------------------

def get_presigned_url(object_key: str) -> Optional[str]:
    headers = {"x-api-gateway-auth": API_KEY, "Content-Type": "application/json"}
    resp = _request("POST", API_POST_URL, headers=headers, json_body={"object_key": object_key})
    if not resp:
        return None
    try:
        data = resp.json()
    except ValueError:
        _dump(resp, "presigned-url NON-JSON")
        return None
    url = data.get("upload_url") or data.get("url") or data.get("presigned_url")
    if not url:
        print("[ERROR] presigned URL missing; see response above")
    return url


def post_jpg(local_path: str, upload_url: str) -> bool:
    headers = {"x-api-gateway-auth": API_KEY, "Content-Type": "image/jpg"}
    with open(local_path, "rb") as f:
        resp = _request("POST", upload_url, headers=headers, data=f)
    if resp:
        print(f"[UPLOAD] image POST success {resp.status_code}")
        return True
    print("[ERROR] image POST failed")
    return False


def post_meta(meta: dict):
    headers = {"x-api-gateway-auth": API_KEY, "Content-Type": "application/json"}
    _request("POST", API_POST_URL, headers=headers, json_body=meta)

# -----------------------------------------------------------
# Utility
# -----------------------------------------------------------

def _basename(p: str) -> str:
    return os.path.basename(urlparse(p).path if p.startswith(('http','https','file://')) else p)

# -----------------------------------------------------------
# Core routine for one image sequence
# -----------------------------------------------------------

def handle_sequence(crops, classes, boxes, names, args):
    max_h = max(c.shape[0] for c in crops)
    combined = np.hstack([c if c.shape[0]==max_h else np.vstack((c, np.zeros((max_h-c.shape[0], c.shape[1],3), dtype=c.dtype))) for c in crops])
    now = datetime.datetime.now()
    ts_id = now.strftime("%Y_%m_%d_%H_%M_%S")
    ts_h  = now.strftime("%Y-%m-%d %H:%M:%S")
    issue = f"issue_{ts_id}"
    os.makedirs(args.output, exist_ok=True)
    local_img = os.path.join(args.output, f"{issue}.jpg")
    cv2.imwrite(local_img, combined)

    key = os.path.splitext(_basename(local_img))[0]
    url = get_presigned_url(key)
    if not url or not post_jpg(local_img, url):
        return

    x1,y1,x2,y2 = boxes[0]
    meta = {
        "id": issue,
        "timestamp": ts_h,
        "length": int(round(max(x2-x1, y2-y1)/args.pixels_per_cm)),
        "width": int(round(min(x2-x1, y2-y1)/args.pixels_per_cm)),
        "position": args.position,
        "material": args.material,
        "crack_type": names[max(set(classes), key=classes.count)],
        "crack_location": random.choice([chr(c) for c in range(65,91)]),
        "image_url": url,
    }
    # save local JSON
    try:
        with open(os.path.join(args.output, f"{issue}.json"), "w", encoding="utf-8") as jf:
            json.dump(meta, jf, indent=2, ensure_ascii=False)
        print(f"[LOCAL] saved {issue}.json")
    except Exception as e:
        print("[ERROR] cannot save JSON:", e)
    post_meta(meta)
    print(f"[DONE] {issue} full cycle✅")

# -----------------------------------------------------------
# Folder mode
# -----------------------------------------------------------

def process_folder(folder: str, model: YOLO, args):
    img_paths = sorted([os.path.join(folder,f) for f in os.listdir(folder) if f.lower().endswith((".jpg",".jpeg",".png"))])
    buffer=[]
    for path in img_paths:
        tick = time.time()
        img = cv2.imread(path)
        res = model.predict(source=path, conf=args.conf, save=False)[0]
        boxes=[list(map(int,b.tolist())) for b in res.boxes.xyxy]
        cls=[int(c) for c in res.boxes.cls.tolist()]
        names=res.names
        if not boxes:
            continue
        buffer.append((img, boxes, cls))
        if any(x1<=args.left_threshold for x1,*_ in boxes):
            continue
        crops, classes = [], []
        for im,bx,cl in buffer:
            x1,y1,x2,y2 = bx[0]
            crops.append(im[y1:y2, x1:x2])
            classes.extend(cl)
        handle_sequence(crops, classes, boxes, names, args)
        buffer.clear()
        time.sleep(max(0,1-(time.time()-tick)))
    print("[FOLDER] processing complete")

# -----------------------------------------------------------
# Live camera mode
# -----------------------------------------------------------

def process_camera(dev: str, model: YOLO, args):
    cap=cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"[ERROR] cannot open camera {dev}")
        return
    buffer=[]
    try:
        while True:
            tick=time.time()
            ret,frame=cap.read()
            if not ret:
                time.sleep(0.1); continue
            try:
                res=model.predict(source=frame, conf=args.conf, save=False)[0]
            except Exception as e:
                print("[ERROR] YOLO predict:", e); traceback.print_exc(); continue
            boxes=[list(map(int,b.tolist())) for b in res.boxes.xyxy]
            cls=[int(c) for c in res.boxes.cls.tolist()]
            names=res.names
            if not boxes:
                time.sleep(max(0,1-(time.time()-tick))); continue
            buffer.append((frame.copy(), boxes, cls))
            if any(x1<=args.left_threshold for x1,*_ in boxes):
                time.sleep(max(0,1-(time.time()-tick))); continue
            crops, classes=[],[]
            for fr,bx,cl in buffer:
                x1,y1,x2,y2=bx[0]
                crops.append(fr[y1:y2,x1:x2])
                classes.extend(cl)
            handle_sequence(crops, classes, boxes, names, args)
            buffer.clear()
            time.sleep(max(0,1-(time.time()-tick)))
    except KeyboardInterrupt:
        print("[CAM] user interrupted")
    finally:
        cap.release()
        print("[CAM] complete")

# -----------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------

def main():
    ap=argparse.ArgumentParser("Realtime crack detection → presigned S3")
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", help="Folder with images for batch processing")
    mode.add_argument("--camera", help="Video device", default=None)
    ap.add