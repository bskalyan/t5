from typing_extensions import Optional, Dict  # Use typing_extensions instead
from typing import List
from ss_llm.utils.ss_functions import writelog
import json
import os
from datetime import datetime
import streamlit as st

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

    def get_outputs(self, user: str | None = None) -> Dict[str, list]:  # Alternative syntax without Optional
        filtered = self._read_existing_data(self.filtered_path)
        unfiltered = self._read_existing_data(self.unfiltered_path)
        
        if user:
            filtered = [entry for entry in filtered if entry["user"] == user]
            unfiltered = [entry for entry in unfiltered if entry["user"] == user]
            
        return {
            "filtered": filtered,
            "unfiltered": unfiltered
        }
