from src.server import start_working_on
try:
    print(f"Type: {type(start_working_on)}")
    if hasattr(start_working_on, "fn"):
        print("Has .fn")
    if hasattr(start_working_on, "__wrapped__"):
        print("Has .__wrapped__")
    if callable(start_working_on):
        print("Is callable")
    else:
        print("Not callable")
except Exception as e:
    print(e)
