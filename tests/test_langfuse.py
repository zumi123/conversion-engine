from langfuse import Langfuse
from dotenv import load_dotenv
import os

load_dotenv()

langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ["LANGFUSE_HOST"]
)

# Test auth
auth = langfuse.auth_check()
print("Auth check:", auth)

# Create trace id
trace_id = langfuse.create_trace_id()
print("Trace ID:", trace_id)

# Set trace context first then create observation
with langfuse.start_as_current_observation(
    name="test-trace",
    input={"message": "Hello from Conversion Engine"},
    output={"status": "success"}
):
    # Update the current span with metadata
    langfuse.update_current_span(
        metadata={"test": "pre-flight check"}
    )
    print("Observation created!")

langfuse.flush()
print("Trace sent to Langfuse successfully!")