def linux_linebreaks(source):
    """Convert Windows CRLF, Mac CR and <br>'s in the input string to \n"""
    result = source.replace('\r\n', '\n').replace('\r', '\n')
    # There are multiple valid variants of HTML breaks
    result = result.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    return result


def int_or_none(value):
    """Convert value into int, or return None if not valid. Note that this
    receives input from internet. Python 3 has no issues with long ints."""
    result = None
    try:
        result = int(value)
    except TypeError:
        result = None
    except ValueError:
        result = None
    return result
