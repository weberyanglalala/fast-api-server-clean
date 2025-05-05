def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.
    
    Args:
        text: The string to convert
        
    Returns:
        A URL-friendly slug
    
    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("This is a Test")
        'this-is-a-test'
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")
    
    # Remove special characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    
    # Remove duplicate hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    
    # Remove leading and trailing hyphens
    slug = slug.strip("-")
    
    return slug