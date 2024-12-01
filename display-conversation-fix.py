async def display_conversation(state, streamGenerator):
    """Display the conversation including both user and bot messages"""
    if not streamGenerator:
        for message in state.messages:
            if message["role"] == "user":
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
            if message["role"] == "appName":
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

        # Save outputs using JSONOutputHandler
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
        
        st.session_state["answer"] = answer
        st.html(f'''<input type="text" id="markdown-copy" value="{output_content}" style="opacity: 0; " >''')
        st.session_state["modified_question"] = st.session_state["question"]
        st.session_state.chat_history.append(AIMessage(content=answer))
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})
        st.session_state.messages.append({"role": "appName", "content": answer, "avatar": avatar_bot, "source": "Source here"})
