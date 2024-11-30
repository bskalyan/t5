# STEP 1: REMOVE these functions and sections:
# Remove the append_data and read_existing_data functions since we'll use JSONOutputHandler
def read_existing_data(file_path):  # Remove this
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)
    else:
        existing_data = []
    return existing_data

def append_data(file_path, new_data):  # Remove this
    existing_data = read_existing_data(file_path)
    existing_data.extend(new_data)
    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

# STEP 2: ADD the new JSONOutputHandler class at the top of the file
import json
from datetime import datetime
from typing import Dict, Any, Optional

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
        if '<output>' in answer and '</output>' in answer:
            filtered_output = extract_output_content(answer)
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

    def get_outputs(self, user: Optional[str] = None) -> Dict[str, list]:
        filtered = self._read_existing_data(self.filtered_path)
        unfiltered = self._read_existing_data(self.unfiltered_path)
        
        if user:
            filtered = [entry for entry in filtered if entry["user"] == user]
            unfiltered = [entry for entry in unfiltered if entry["user"] == user]
            
        return {
            "filtered": filtered,
            "unfiltered": unfiltered
        }

# STEP 3: MODIFY the stream_response section to save both outputs
# Find this section:
if not streamGenerator:
    answer = await stream_response(streamGenerator)
    st.session_state.display_buttons = True
    updateCount()

    # REPLACE the feedback section with:
    json_handler = JSONOutputHandler()
    json_handler.save_outputs(
        user=user,
        question=st.session_state["question"],
        answer=answer,
        session_id=st.session_state.session_id
    )

# STEP 4: REPLACE the getPastSessions function with this new version:
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
                "content": output["answer"],  # This is already filtered
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

# STEP 5: REMOVE these lines when they appear:
feedback = [{
    "user": user,
    "user_question": st.session_state["modified_question"],
    "user_feedback": st.session_state["modified_answer"],
    "user_feedback_full": st.session_state["answer"]
}]

feedback_path = "tb_hitl.json"
append_data(feedback_path, feedback)
add_to_vectordb_hitl(feedback[0])
