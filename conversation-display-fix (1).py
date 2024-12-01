# Find this section in your code and replace it with:
if user_input:
    st.session_state.display_buttons = False
    writelog(f"{user} user input : {user_input}")
    input_to_stream_time = time.time()
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    
    # REST CALL TO PASS INPUT TO BACKEND
    streamResponse = fetch_stream(user_input)
    
    # Display user message
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input, 
        "avatar": avatar_user, 
        "source": ""
    })
    st.session_state.chat_history.append(HumanMessage(content=user_input))

    if st.session_state["messages"]:
        await display_conversation(st.session_state, None)
        instruction = {
            "input": user_input, 
            "chat_history": st.session_state.chat_history
        }
        
        if st.session_state["messages"]:
            await display_conversation(st.session_state, streamResponse)
            writelog("Time from input to streaming end is: " + str(time.time() - input_to_stream_time))
            st.session_state["disabledButtons"] = False
