import threading

def run_in_thread(target_func, *args, **kwargs):
    """
    Runs the specified function in a separate background thread.

    Args:
        target_func (function): The function to be executed in the background thread.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.
        
    The function is executed as a daemon thread, meaning it will automatically terminate 
    when the main program exits.
    """
    threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True).start()

def run_with_callback(target_func, callback_func=None, *args, **kwargs):
    """
    Runs a target function in a separate thread and, upon completion, 
    executes a callback function if provided.

    Args:
        target_func (function): The function to execute in the thread.
        callback_func (function): A function to call after target_func completes.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.
    """
    def wrapper():
        result = target_func(*args, **kwargs)
        if callback_func:
            callback_func(result)

    threading.Thread(target=wrapper, daemon=True).start()

def run_with_exception_handling(target_func, *args, **kwargs):
    """
    Runs a target function in a separate thread with basic exception handling.

    Args:
        target_func (function): The function to execute in the thread.
        *args: Positional arguments to pass to the target function.
        **kwargs: Keyword arguments to pass to the target function.
    """
    def wrapper():
        try:
            target_func(*args, **kwargs)
        except Exception as e:
            print(f"An error occurred in thread: {e}")

    threading.Thread(target=wrapper, daemon=True).start()
