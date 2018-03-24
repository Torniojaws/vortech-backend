def linux_linebreaks(source):
    """Convert Windows CRLF, Mac CR and <br>'s in the input string to \n"""
    result = source.replace('\r\n', '\n').replace('\r', '\n')
    # There are multiple valid variants of HTML breaks
    result = result.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    return result
