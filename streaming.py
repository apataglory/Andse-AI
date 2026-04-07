from flask import Response, stream_with_context

class StreamManager:
    """
    Utilities for high-performance data streaming.
    """

    @staticmethod
    def stream_text_generator(generator_func):
        """
        Wraps a generator function for Flask HTTP streaming.
        Useful if we want a non-WebSocket endpoint (e.g., for curl).
        """
        @stream_with_context
        def generate():
            for chunk in generator_func():
                # Server-Sent Events (SSE) format
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        
        return Response(generate(), mimetype='text/event-stream')

    @staticmethod
    def stream_file_chunks(file_path, chunk_size=4096):
        """
        Streams a large file (video/audio) in chunks to save RAM.
        """
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

# Global Instance
stream_manager = StreamManager()