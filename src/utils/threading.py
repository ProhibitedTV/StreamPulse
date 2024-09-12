"""
threading.py

This module provides utility functions for running tasks in the background using 
concurrent threads. It utilizes the `ThreadPoolExecutor` to manage a pool of threads 
for executing functions asynchronously, handling callbacks, and managing timeouts.

Functions:
    run_in_thread - Runs a specified function in a separate background thread.
    run_with_callback - Runs a function in a thread and executes a callback upon completion.
    run_with_exception_handling - Runs a function in a thread with exception handling.
    run_in_thread_with_timeout - Runs a function in a thread with a timeout.
    shutdown_executor - Shuts down the thread pool executor.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Thread pool executor to reuse threads
executor = ThreadPoolExecutor(max_workers=5)

def _submit_task(target_func, *args, **kwargs):
    """
    A helper function to submit a task to the thread pool executor.

    Args:
        target_func (function): The function to be executed in the background thread.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
    """
    try:
        return executor.submit(target_func, *args, **kwargs)
    except Exception as e:
        logging.error(f"Failed to submit task: {e}", exc_info=True)
        return None

def run_in_thread(target_func, *args, **kwargs):
    """
    Runs the specified function in a separate background thread using ThreadPoolExecutor.
    Returns a Future object.

    Args:
        target_func (function): The function to be executed in the background thread.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
    """
    logging.debug(f"Running function '{target_func.__name__}' in a new thread.")
    return _submit_task(target_func, *args, **kwargs)

def run_with_callback(target_func, callback_func=None, *args, **kwargs):
    """
    Runs a target function in a separate thread using ThreadPoolExecutor and executes a callback upon completion.

    Args:
        target_func (function): The function to execute in the thread.
        callback_func (function, optional): A function to call after target_func completes.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.

    Returns:
        Future: A Future object representing the execution of the function.
    """
    future = executor.submit(target_func, *args, **kwargs)
    
    # Define the callback function to be called upon completion
    if callback_func:
        future.add_done_callback(lambda fut: callback_func(fut))
    
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
            logging.debug(f"Running function '{target_func.__name__}' with exception handling.")
            return target_func(*args, **kwargs)
        except Exception as e:
            logging.error(f"An error occurred in thread '{target_func.__name__}': {e}", exc_info=True)

    return _submit_task(wrapper, *args, **kwargs)

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
    future = _submit_task(target_func, *args, **kwargs)
    
    if not future:
        return None
    
    try:
        result = future.result(timeout=timeout)
        return result
    except TimeoutError:
        logging.error(f"Thread execution timed out after {timeout} seconds for function '{target_func.__name__}'.")
    except Exception as e:
        logging.error(f"Error occurred while running function '{target_func.__name__}': {e}", exc_info=True)
    
    return None

def shutdown_executor(wait=True):
    """
    Shuts down the thread pool executor gracefully, ensuring no new tasks are scheduled and existing tasks are completed.

    Args:
        wait (bool): If True, wait for tasks to complete before shutting down.
                     If False, the executor will attempt to shutdown immediately.
    """
    logging.info("Shutting down thread pool executor.")
    executor.shutdown(wait=wait)
    logging.info("Thread pool executor has been shut down.")
