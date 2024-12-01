# Add this at the top of your file with other utility functions
def extract_output_content(message: str) -> str:
    """
    Extract content between <output> tags from a message.
    
    Args:
        message (str): Message containing output tags
        
    Returns:
        str: Content between output tags, or original message if no tags found
    """
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

# Update the JSONOutputHandler to use this function
class JSONOutputHandler:
    def __init__(self, filtered_path: str = "filtered_outputs.json", 
                 unfiltered_path: str = "unfiltered_outputs.json"):
        self.filtered_path = filtered_path
        self.unfiltered_path = unfiltered_path

    # ... (previous methods remain the same)

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
