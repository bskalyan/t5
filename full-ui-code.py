###TODO###
# Session history needs to be added to conversation history when user pulls session history.

from ss_llm.utils.ss_functions import writelog
import streamlit as st
import httpx
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import os
import base64
import time
import torch
import gc
from threading import Thread
from langchain_core.messages import HumanMessage, AIMessage
from time import sleep
import socket

# Add the JSONOutputHandler class
class JSONOutputHandler:
    def __init__(self, filtered_path: str = "filtered_outputs.json", 
                 unfiltered_path: str = "unfiltered_outputs.json"):
        self.filtered_path = filtered_path
        self.unfiltered_path = unfiltered_path

    def _read_existing_data(self, file_path: str) -> list:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                writelog(f"Error reading {file_path}, starting with empty list", level="Warning")
                return []
        return []

    def _write_data(self, data: list, file_path: str):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def save_outputs(self, user: str, question: str, answer: str, session_id: str):
        timestamp = datetime.now().isoformat()
        unfiltered_data = self._read_existing_data(self.unfiltered_path)
        
        # Save unfiltered output
        unfiltered_entry = {
            "timestamp": timestamp,
            "user": user,
            "question": question,
            "answer": answer,
            "session_id": session_id
        }
        unfiltered_data.append(unfiltered_entry)
        self._write_data(unfiltered_data, self.unfiltered_path)
        
        # Extract and save filtered output
        filtered_output = extract_output_content(answer)
        if filtered_output != answer:  # Only save if output tags were found
            filtered_data = self._read_existing_data(self.filtered_path)
            filtered_entry = {
                "timestamp": timestamp,
                "user": user,
                "question": question,
                "answer": filtered_output,
                "session_id": session_id
            }
            filtered_data.append(filtered_entry)
            self._write_data(filtered_data, self.filtered_path)
            writelog(f"Saved filtered output for user: {user}")
        
        writelog(f"Saved unfiltered output for user: {user}")

    def get_outputs(self, user: str | None = None) -> Dict[str, list]:
        filtered = self._read_existing_data(self.filtered_path)
        unfiltered = self._read_existing_data(self.unfiltered_path)
        
        if user:
            filtered = [entry for entry in filtered if entry["user"] == user]
            unfiltered = [entry for entry in unfiltered if entry["user"] == user]
            
        return {
            "filtered": filtered,
            "unfiltered": unfiltered
        }

def extract_output_content(message: str) -> str:
    """Extract content between <output> tags"""
    start_tag = "<output>"
    end_tag = "</output>"
    start_index = message.find(start_tag)
    end_index = message.find(end_tag)
    
    if start_index != -1 and end_index != -1:
        start_index += len(start_tag)
        output_content = message[start_index:end_index].strip()
        return output_content
    
    print("Output ::: ---> No <output> content found.")
    return message

async def fetch_stream(question):
    async with httpx.AsyncClient(timeout=None) as client:
        writelog(f"{user} | Inside fetch_stream start")
        json_input = {
            'input': {
                'question': question
            },
            'conversation_history': [*st.session_state.conversation_history],
            'user': user
        }
        try:
            async with client.stream("POST", databricks_url, json=json_input) as response:
                async for chunk in response.aiter_text():
                    line, stream_flag, context = json.loads(chunk)
                    yield line, stream_flag, context
        except Exception as err:
            writelog(f"{user}Unexpected {err=}, {type(err)=}")
            raise

def getPastSessions(user):
    """Get past sessions from filtered output JSON"""
    json_handler = JSONOutputHandler()
    outputs = json_handler.get_outputs(user)
    filtered_outputs = outputs["filtered"]
    
    # Group by session_id
    sessions = {}
    for output in filtered_outputs:
        session_id = output.get("session_id", session_id_notFoundError)
        if session_id not in sessions:
            sessions[session_id] = []
        
        sessions[session_id].extend([
            {
                "session_id": session_id,
                "role": "user",
                "content": output["question"],
                "avatar": "user_url",
                "source": " ",
                "timestamp": output["timestamp"]
            },
            {
                "session_id": session_id,
                "role": "appName",
                "content": output["answer"],
                "avatar": "bot_url",
                "source": "Source here",
                "timestamp": output["timestamp"]
            }
        ])
    
    # Convert to list and sort by timestamp
    past_sessions = list(sessions.values())
    for session in past_sessions:
        session.sort(key=lambda x: x["timestamp"])
    
    past_sessions.sort(key=lambda x: x[0]["timestamp"] if x else "", reverse=True)
    return past_sessions

async def stream_response(streamGenerator):
    output_started = False
    output_ended = False
    message_alignment = "flex-start"
    message_bg_color = "#acb6bd"
    avatar_class = "bot-avatar"
    avatar_url = avatar_bot
    container = st.empty()
    text_placeholder = st.empty()
    result_text = ""
    output = ""
    streamed_text = ""

    async for data, stream_flag, context in streamGenerator:
        if not stream_flag:
            result_text += data
            if '<output>' in data:
                output_started = True
            if '</output>' in data:
                output_ended = True

            if output_started:
                output += data
                if '</output>' in output:
                    output_ended = False
                    content = output.split('<output>', 1)[1]
                    for char in content:
                        streamed_text += char
                        result = f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                            <img src="data:image/png;base64,{bot_url}" class="{avatar_class}" alt="avatar" style="width: 60px; height: 60px;" />
                            <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; margin-left: 5px; max-width: 75%; font-size: 17px;">{streamed_text} \n </div>
                        </div>
                        """
                        container.write(result, unsafe_allow_html=True)
                        await asyncio.sleep(0.05)

            if output_started and output_ended:
                output += data
                content = output.split('</output>', 1)[0]
                for char in content:
                    streamed_text += char

                result = f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <img src="data:image/png;base64,{bot_url}" class="{avatar_class}" alt="avatar" style="width: 60px; height: 60px;" />
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; margin-left: 5px; max-width: 75%; font-size: 17px;">{streamed_text} \n </div>
                </div>
                """
                container.write(result, unsafe_allow_html=True)
                await asyncio.sleep(0.05)
                break

    if '<output>' not in output and '</output>' not in output:
        content = result_text
        for char in content:
            streamed_text += char
            result = f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                <img src="data:image/png;base64,{bot_url}" class="{avatar_class}" alt="avatar" style="width: 60px; height: 60px;" />
                <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; margin-left: 5px; max-width: 75%; font-size: 17px;">{streamed_text} \n </div>
            </div>
            """
            container.write(result, unsafe_allow_html=True)
            await asyncio.sleep(0.05)
    else:
        with st.expander("See reference context below", expanded=False):
            extracted_context = extract_output_content(context)
            if "No <output> content found." in extracted_context:
                extracted_context = context
            st.write(extracted_context)
    return result_text

async def display_conversation(history, streamGenerator):
    if not streamGenerator:
        for message in history.messages:
            if message["role"] == user:
                avatar_url = user_url
                message_alignment = "flex-end"
                message_bg_color = "linear-gradient(135deg, #00B2FF 0%, #006AFF 100%)"
                avatar_class = "user-avatar"
                st.write(
                    f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                        <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; margin-left: 5px; max-width: 75%; font-size: 17px;">
                            {message["content"]} \n </div>
                        <img src="data:image/png;base64,{user_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if message["role"] == appName:
                message_alignment = "flex-start"
                message_bg_color = "#acb6bd"
                avatar_class = "bot-avatar"
                avatar_url = avatar_bot
                text = message["content"]
                if '<output>' in text and '</output>' in text:
                    text = extract_output_content(text)
                text = format_message(text)
                st.write(
                    f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                        <img src="data:image/png;base64,{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                        <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; margin-left: 5px; max-width: 75%; font-size: 17px;">
                            {text} \n </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        answer = await stream_response(streamGenerator)
        st.session_state.display_buttons = True
        updateCount()
        
        # Add the new JSON handler code here
        json_handler = JSONOutputHandler()
        json_handler.save_outputs(
            user=user,
            question=st.session_state["question"],
            answer=answer,
            session_id=st.session_state.session_id
        )
        
        output_content = ""
        if '<output>' in answer and '</output>' in answer:
            output_content = extract_output_content(answer)
            print("answer when extracted answer:---->", answer)
        
        writelog(f"{user} Generated answer for user question : \n\n" + answer + "\n\n")
        st.session_state["answer"] = answer
        st.html(f'''<input type="text" id="markdown-copy" value="{output_content}" style="opacity: 0; " >''')
        st.session_state["modified_question"] = st.session_state["question"]
        st.session_state.chat_history.append(AIMessage(content=answer))
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})
        st.session_state.messages.append({"role": "appName", "content": answer, "avatar": avatar_bot, "source": "Source here"})

# Keep the rest of your existing code (authentication, UI setup, etc.) the same...
