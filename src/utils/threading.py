import threading

def run_in_thread(target_func, *args, **kwargs):
    threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True).start()
