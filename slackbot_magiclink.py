import json
import requests

from urllib.parse import urlparse, parse_qs
from datetime import datetime

from slackbot_google_integration import get_transcript

def get_latest_video(sessions):
    latest_session = max(sessions, key=lambda s: datetime.fromisoformat(s["session_date"].replace("Z", "+00:00")))
    latest_info = {
        "session_date": latest_session["session_date"],
        "youtube_link": latest_session.get("youtube_link", []),
        "instructor_names": latest_session.get("instructor_names", []),
        "session_summary": latest_session.get("session_summary", []),
        "project_name": latest_session.get("project_name", ""),
        "time_zone": latest_session.get("time_zone", "")
    }
    #print(f"Latest info: {latest_info} ")
    return latest_info

def extract_ml_content_video(rsp_json):
    sessions=rsp_json['data']['sessions']
    latest_session=get_latest_video(sessions)
    first_video=latest_session['youtube_link']
    if isinstance(first_video, list):
        first_video=first_video[0]
    new_list=[]
    for sess in sessions:
        new_list.append({"date":sess['session_date'],"summary":str(sess['session_summary'])})

    return new_list, first_video

def get_video_id_from_url(url):
    url_chunks = urlparse(url)
    if not url_chunks.query:
        video_id = url_chunks.path.split("/")[-1]
        return video_id

    video_id = parse_qs(url_chunks.query).get("v", [""])[0]

    if not video_id:
        video_id = url_chunks.path.split("/")[-1]
        return video_id

    return video_id


def process_ml(req_url:str):
    SRC_URL="https://apigateway.navigator.pyxeda.ai/aiclub/one-on-one-student-info?linkId="
    print(f"PROCESS_ML:  {req_url=}")
    response=requests.get(req_url)
    #st.write(f"Status code: {response.status_code}")
    rsp_json=json.loads(response.text)
    mlc,fyv=extract_ml_content_video(rsp_json)
    video_id=get_video_id_from_url(fyv)
    video_transcript=get_transcript(video_id)
    return video_transcript,mlc