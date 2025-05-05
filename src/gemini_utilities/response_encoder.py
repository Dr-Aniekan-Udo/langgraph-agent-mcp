import json


class CustomEncoder(json.JSONEncoder):
    """A custom json encoder that handles object with content attribute

    Args:
        json (json): If an object as the attribute content, It decompose it to a dictionary
        returns the dictionary or default value if no content is present
    """
    def default(self, o):
        if hasattr(o, "content"):
            return {"type": o.__class__.__name__, "content": o.content}
        return super().default(o)
