from typing import Any, Callable, TypeVar
from uuid import UUID
import inspect
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from src.app.ui_component import display_message, display_info

class StreamHandler(BaseCallbackHandler):
    def __init__(self):
        # Initialize separate containers for tool output and LLM text
        self.tool_container = st.empty()
        self.llm_container = st.empty()

    def on_tool_end(self, output: Any, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        """
        Handle the end of a tool execution by updating the last message's info
        with the tool's output and displaying this information.
        """
        print(f"Tool output: {output}")
        # Convert the output to a string to store in the info dictionary
        info_content = str(output)
        info = {"tool_output": info_content}

        # Update the last message's info with the tool's output
        if hasattr(st.session_state, 'memory_handler') and len(st.session_state.memory_handler) > 0:
            st.session_state.memory_handler.update_last_info(info)

        # Display the updated info in the tool container
        display_info(info, container=self.tool_container)

    def on_llm_new_token(self, token: str, **kwargs):
        st.session_state.memory_handler.append_last_message(token)
        message, _ = st.session_state.memory_handler[-1]
        # Display the message in the LLM container
        display_message(message, container=self.llm_container)

def get_streamhandler_cb() -> BaseCallbackHandler:
    """
    Creates a StreamHandler callback handler that integrates fully with any LangChain ChatLLM integration.
    This function ensures that all callback methods run within the Streamlit execution context,
    fixing the NoSessionContext() error commonly encountered in Streamlit callbacks.

    Returns:
        BaseCallbackHandler: An instance of StreamHandler configured for full integration
                             with ChatLLM, enabling dynamic updates in the Streamlit app.
    """

    # Define a type variable for generic type hinting in the decorator, ensuring the original
    # function and wrapped function maintain the same return type.
    fn_return_type = TypeVar('fn_return_type')

    # Decorator function to add Streamlit's execution context to a function
    def add_streamlit_context(fn: Callable[..., fn_return_type]) -> Callable[..., fn_return_type]:
        """
        Decorator to ensure that the decorated function runs within the Streamlit execution context.
        This is necessary for interacting with Streamlit components from within callback functions
        and prevents the NoSessionContext() error by adding the correct session context.

        Args:
            fn (Callable[..., fn_return_type]): The function to be decorated, typically a callback method.
        Returns:
            Callable[..., fn_return_type]: The decorated function that includes the Streamlit context setup.
        """
        # Retrieve the current Streamlit script execution context.
        # This context holds session information necessary for Streamlit operations.
        ctx = get_script_run_ctx()

        def wrapper(*args, **kwargs) -> fn_return_type:
            """
            Wrapper function that adds the Streamlit context and then calls the original function.
            If the Streamlit context is not set, it can lead to NoSessionContext() errors, which this
            wrapper resolves by ensuring that the correct context is used when the function runs.

            Args:
                *args: Positional arguments to pass to the original function.
                **kwargs: Keyword arguments to pass to the original function.
            Returns:
                fn_return_type: The result from the original function.
            """
            # Add the previously captured Streamlit context to the current execution.
            # This step fixes NoSessionContext() errors by ensuring that Streamlit knows which session
            # is executing the code, allowing it to properly manage session state and updates.
            add_script_run_ctx(ctx=ctx)
            return fn(*args, **kwargs)  # Call the original function with its arguments

        return wrapper

    # Create an instance of your StreamHandler
    stream_handler = StreamHandler()

    # Iterate over all methods of the StreamHandler instance
    for method_name, method_func in inspect.getmembers(stream_handler, predicate=inspect.ismethod):
        if method_name.startswith('on_'):  # Identify callback methods that respond to LLM events
            # Wrap each callback method with the Streamlit context setup to prevent session errors
            setattr(stream_handler, method_name,
                    add_streamlit_context(method_func))  # Replace the method with the wrapped version

    # Return the fully configured StreamHandler instance, now context-aware and integrated with any ChatLLM
    return stream_handler


