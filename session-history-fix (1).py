def append_session_history(file_path: str, new_data: list, session_id: str, is_new_session: bool = False):
    """
    Append session history to JSON file
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)
    else:
        existing_data = [[]]

    # If it's a new session and there's existing data
    if is_new_session:
        if not existing_data[0]:
            existing_data[0].extend(new_data)
        else:
            existing_data.append(new_data)
    
    # If it's an existing session
    elif not existing_data[0]:
        existing_data[0].extend(new_data)
    else:
        # Find and update existing session
        for session in existing_data:
            if session and isinstance(session, list) and len(session) > 0 and session[0].get("session_id") == session_id:
                session.extend(new_data)
                break

    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

# Then in your display_conversation function, replace the append_session_history calls with:
async def display_conversation(history, streamGenerator):
    # ... previous code ...
    else:
        answer = await stream_response(streamGenerator)
        st.session_state.display_buttons = True
        updateCount()
        
        # Save both outputs using JSONOutputHandler
        json_handler = JSONOutputHandler()
        json_handler.save_outputs(
            user=user,
            question=st.session_state["question"],
            answer=answer,
            session_id=st.session_state.session_id
        )
        
        # Update chat history
        output_content = ""
        if '<output>' in answer and '</output>' in answer:
            output_content = extract_output_content(answer)
        
        writelog(f"{user} Generated answer for user question : \n\n" + answer + "\n\n")
        st.session_state["answer"] = answer
        st.html(f'''<input type="text" id="markdown-copy" value="{output_content}" style="opacity: 0; " >''')
        st.session_state["modified_question"] = st.session_state["question"]
        st.session_state.chat_history.append(AIMessage(content=answer))
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})
        st.session_state.messages.append({"role": "appName", "content": answer, "avatar": avatar_bot, "source": "Source here"})
        
        # Append user message to session history
        append_session_history(
            sessionHistoryPath,
            [{
                "session_id": st.session_state.session_id,
                "role": "user",
                "content": user_input,
                "avatar": "user_url",
                "source": " "
            }],
            st.session_state.session_id
        )
        
        # Append bot response to session history
        append_session_history(
            sessionHistoryPath,
            [{
                "session_id": st.session_state.session_id,
                "role": "appName",
                "content": answer,
                "avatar": "bot_url",
                "source": "Source here"
            }],
            st.session_state.session_id
        )
