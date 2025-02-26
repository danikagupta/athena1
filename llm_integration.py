from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import os
import streamlit as st

from datetime import date

from typing import TypedDict, Annotated, List, Dict, Any, Union, Optional
from pydantic import BaseModel

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage

class ActionItem(TypedDict):
    action: str
    owner: str
    team: str
    dueDate: str

class ActionItemList(BaseModel):
    itemCategory: str
    itemList: List[ActionItem]


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

OPENAI_MODEL = "gpt-4o-mini"

def create_llm_message(userinput_record):
    PROMPT_TEMPLATE=f"""
        You are an Executive Administrator with strong expertise in creating Action Items.

        Based on user query, accurately classify customer requests into one of the following categories based on context
        and content, even if specific keywords are not used.
        1. SmallTalk
        2. ActionItems
        3. Information
        4. Other

        For ActionItems, extract the following information:
        - Action
        - Owner
        - Team
        - Due Date

        Team can be any of the following: Engineering, Marketing, Sales, Support, Operations, Finance, Legal, HR, Coordinator, Other
        For "Schedule weekly meeting for Therapy project", Team should be Coordinator.

        Today is {date.today()}. If you do not know teh due date for an item, assume one week from today.
    """

    msgList=[
        SystemMessage(PROMPT_TEMPLATE),
        HumanMessage(str(userinput_record))
    ]

    return msgList

    #return f"User {userinput_record['name']} with email {userinput_record['email']} and role {userinput_record['role']} said: {userinput_record['user_input']}"


def llm_process(userinput_record):
    model = ChatOpenAI(model=OPENAI_MODEL, temperature=0, api_key=OPENAI_API_KEY)
    llm_message=create_llm_message(userinput_record)
    llm_response=model.with_structured_output(ActionItemList).invoke(llm_message)
    st.write(f"llm_response={llm_response}")
    if llm_response.itemCategory=="ActionItems":
        return llm_response.itemList
    else:
        return []
 