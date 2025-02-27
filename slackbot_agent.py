from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, List, Dict, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import random

from slack_integration import get_student_list
from slackbot_magiclink import process_ml

from enum import Enum
import json

SRC_PREFIX="https://apigateway.navigator.pyxeda.ai/aiclub/one-on-one-student-info?linkId="

class AgentState(TypedDict):
    agent: str
    message: str
    responseToUser: str
    category: str
    profile:Dict
    channel_history:List
    message_ts:str
    url:str
    student_name:str
    video_transcript:str
    mlc:str


class CategoryEnum(str, Enum):
    complaint = "Complaint"
    sales = "Sales"
    testimonial = "Testimonial"
    other = "Other"

class CategoryGroup(BaseModel):
    category_name: CategoryEnum = Field(description="The category of the item or request.")
    model_config = ConfigDict(
        title="CategoryGroup",
        description="A simple model capturing the user's category."
    )

json_schema_classifier = {
    "title": "CategoryGroup",
    "description": "Category of the user request",
    "type": "object",
    "properties": {
        "category_name": {
            "type": "string",
            "description": "The category of the item or request",
        },
        "student_name": {
            "type": "string",
            "description": "The name of the student",
        },
        "session_date": {
            "type": "string",
            "description": "The name of the student",
        },
    },
    "required": ["category_name"],
}


json_schema_student = {
    "title": "StudentUrl",
    "description": "URL for the student",
    "type": "object",
    "properties": {
        "student_name": {
            "type": "string",
            "description": "The name of the student",
        },
        "link_id": {
            "type": "string",
            "description": "The link-id for the student",
        },
    },
    "required": ["url"],
}

#class CategoryGroup(BaseModel):
#    category_name: str= Field(description="The category of the item or request.")

def create_llm_message(system_prompt:str, state:AgentState):
    resp = []
    resp.append(SystemMessage(content=system_prompt))
    category=state.get("category")

    channel_history = state.get("channel_history")
    if channel_history:
        history_json=json.dumps(channel_history)
        resp.append(HumanMessage(content=f"Here is the conversation history: \n{history_json}"))
    video_transcript=state.get("video_transcript")
    if video_transcript:
        if category=="Session":
            resp.append(HumanMessage(content=f"Here is the video transcript for the last session: \n{video_transcript}"))
    mlc=state.get("mlc")
    if mlc:
        if category=="Student":
            resp.append(HumanMessage(content=f"Here is the student's session history: \n{mlc}"))
    resp.append(HumanMessage(content=state.get("message")))
    # print(f"CREATE LLM MESSAGE: {resp=}")
    return resp

CLASSIFIER_PROMPT=f"""
You are an expert with deep knowledge of Customer Support.
Your job is to comprehend the message from the user even if it lacks specific keywords,
always maintain a friendly, professional, and helpful tone.

You are asked by teachers to help analyze previous teaching sessions.

Classify the incoming request into one of the following categories based on context
and content, even if specific keywords are not used.
1. If the answer requires knowing about just one session, mark the category as Session.
2. If the answer requires knowing about what student did across many sessions, mark the category as Student.
3. If the user hasn't provided enough information, mark the category as Other.

For Other category, please also request the user to provide more information - the name of the student, as well as whether
the user wants to ask the question in general or about a specific session.

If the user mentions multiple students, pick the latest student that the user talked about.

Examples:
Q: Did they encounter any error while coding?
A: Response should saw category is Session.

Q: Summary of the discussion between instructor and student
A: Response should saw category is Session.

Q: Any action items discussed during the session?
A: Response should saw category is Session.

Q: Do we have to send any email to the student?
A: Response should saw category is Session.

Q: Important details to be noted for the next sessions?
A: Response should saw category is Session.

Q: Was there any issue in the session?if so list them all
A: Response should saw category is Session.

Q: Did the instructor join on time
A: Response should saw category is Session.

Q: Did the instructor sound well prepared for the session?
A: Response should saw category is Session.


Q: What is the students project about?
A: Response should saw category is Student.

Q: What are the students targets, where they have already submitted and want to submit in the future?
A: Response should saw category is Student.

Q: What specific questions would they like the mentor answer in the next session?
A: Response should saw category is Student.

Q: How much time do we have between now and their next target deadline
A: Response should saw category is Student.

"""

STUDENT_PROMPT=f"""
You are an expert with deep knowledge of Customer Support.
Here is the student's session history.
Use this session history to answer the user's questions.
Please remember to be polite, concise, and professional in your response.
"""

SESSION_PROMPT=f"""
You are an expert with deep knowledge of Customer Support.
Please use this session information to answer the user's questions.
Please remember to be polite, concise, and professional in your response.
"""

CATCHALL_PROMPT=f"""
Tell the user that you are here to help them. 
If the user has not provided student information, request the user to provide the name of the student.
If the user wants to enquire about a specific session, ask them to provide the session date.
If the user has provided the student information already, ask whether there is any other student they would like to inquire about.
"""

class FirstAgent:
    def __init__(self, provider:str, model: str, api_key: str):
        if provider == 'OpenAI':
            self.model = ChatOpenAI(model=model, temperature=0, api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        workflow = StateGraph(AgentState)

        workflow.add_node("classifier",self.classifier)
        workflow.add_node("student",self.studentAgent)
        workflow.add_node("session",self.sessionAgent)
        workflow.add_node("catchall",self.catchallAgent)

        workflow.add_edge(START, "classifier")
        workflow.add_conditional_edges("classifier", self.main_router)
        workflow.add_edge("student", END)
        workflow.add_edge("session", END)
        workflow.add_edge("catchall", END)

        self.graph = workflow.compile()

    def classifier(self, state: AgentState):
        llm_messages = create_llm_message(CLASSIFIER_PROMPT,state)
        llm_response = self.model.with_structured_output(json_schema_classifier).invoke(llm_messages)
        category = llm_response.get('category_name')
        student_name = llm_response.get('student_name')
        session_date = llm_response.get('session_date')
        print(f"CLASSIFIER: {category=}, {llm_response=}")

        if student_name:
            student_list=json.dumps(get_student_list())
            msg2=[SystemMessage(content=f"For student: {student_name}, return the link_id from the following list: {student_list}")]
            llm_response_student=self.model.with_structured_output(json_schema_student).invoke(msg2)
            magic_link_url=llm_response_student.get('link_id')
            if magic_link_url:
                video_transcript,mlc=process_ml(SRC_PREFIX+magic_link_url)
                jvt=json.dumps(video_transcript)
                jvt1000=jvt[:1000]
                print(f"CLASSIFIER VIDEO PROCESSING: {len(jvt)=}, {jvt1000}")
                return {"category": category, "url":magic_link_url, "video_transcript":jvt, 
                        "mlc":str(mlc),"student_name":student_name}
            else:
                return {"category": category, "student_name":student_name}
        else:
            return {"category": category}

    def main_router(self, state: AgentState):
        #print(f"MAIN ROUTER: {state=}")
        category = state.get("category")
        print(f"MAIN ROUTER {category=}")
        if category == "Student":
            return "student"
        elif category == "Session":
            return "session"  
        else: 
            return "catchall"

    def studentAgent(self, state: AgentState):

        llm_messages = create_llm_message(STUDENT_PROMPT,state)
        llm_response = self.model.invoke(llm_messages)
        return {"responseToUser": llm_response.content}

    def sessionAgent(self, state: AgentState):
        llm_messages = create_llm_message(SESSION_PROMPT,state)
        llm_response = self.model.invoke(llm_messages)
        return {"responseToUser": llm_response.content}

    def catchallAgent(self, state: AgentState):
        llm_messages = create_llm_message(CATCHALL_PROMPT,state)
        llm_response = self.model.invoke(llm_messages)
        return {"responseToUser": llm_response.content}