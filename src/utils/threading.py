import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Thread pool executor to reuse threads
executor = ThreadPoolExecutor(max_workers=5)

def run_in_thread(target_func, *args, **kwargs):
    """
    Runs the specified function in a separate background thread using ThreadPoolExecutor.

    Args:
        target_func (function): The function to be executed in the background thread.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
    """
    return executor.submit(target_func, *args, **kwargs)

def run_with_callback(target_func, callback_func=None, *args, **kwargs):
    """
    Runs a target function in a separate thread using ThreadPoolExecutor and executes a callback upon completion.

    Args:
        target_func (function): The function to execute in the thread.
        callback_func (function): A function to call after target_func completes.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
    """
    future = executor.submit(target_func, *args, **kwargs)
    
    # Define the callback function to be called upon completion
    if callback_func:
        future.add_done_callback(lambda fut: callback_func(fut.result()))
    
    return future

def run_with_exception_handling(target_func, *args, **kwargs):
    """
    Runs a target function in a separate thread with basic exception handling using ThreadPoolExecutor.

    Args:
        target_func (function): The function to execute in the thread.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
    """
    def wrapper(*args, **kwargs):
        try:
            return target_func(*args, **kwargs)
        except Exception as e:
            logging.error(f"An error occurred in thread: {e}", exc_info=True)

    return executor.submit(wrapper, *args, **kwargs)

def run_in_thread_with_timeout(target_func, timeout, *args, **kwargs):
    """
    Runs the specified function in a separate background thread with a timeout.

    Args:
        target_func (function): The function to execute in the background thread.
        timeout (int): The maximum time allowed for the function to run.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
        If the timeout is reached, the result will be None.
    """
    future = executor.submit(target_func, *args, **kwargs)
    
    try:
        result = future.result(timeout=timeout)
        return result
    except Exception as e:
        logging.error(f"Thread execution timed out or error occurred: {e}", exc_info=True)
        return None
