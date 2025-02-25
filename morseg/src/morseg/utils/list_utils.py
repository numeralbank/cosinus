def list_contains_sublist(full_list: list, partial_list: list):
    """
    method checks whether a given list can be found as complete sequence within another list,
    for example: ['b', 'c'] is a valid sublist of ['a', 'b', 'c', 'd']; but ['a', 'c'] is not.
    :param full_list: the larger list to check
    :param partial_list: the queried sublist
    :return: True if partial_list is a valid sublist of full_list; False otherwise
    """
    if full_list is None or partial_list is None:
        return False

    len_full_list = len(full_list)
    len_partial_list = len(partial_list)

    if len_full_list < len_partial_list:
        return False

    for i in range(len_full_list - len_partial_list + 1):
        if full_list[i:i+len_partial_list] == partial_list:
            return True

    return False


def get_start_idx_for_sublist(full_list: list, partial_list: list):
    """
    Retrieves the start index of a valid sublist within a longer list.
    If the sublist occurs several times, the start index of the first occurrence is returned.
    :param full_list: the larger list to check
    :param partial_list: the queried sublist
    :return: the start index of partial_list if it is a valid sublist of full_list; -1 otherwise.
    """
    if full_list is None or partial_list is None:
        return -1

    len_full_list = len(full_list)
    len_partial_list = len(partial_list)

    if len_full_list < len_partial_list:
        return -1

    for i in range(len_full_list - len_partial_list + 1):
        if full_list[i:i + len_partial_list] == partial_list:
            return i

    return -1


def remove_and_insert_placeholder(full_list: list, partial_list: list, placeholder):
    """
    Removes a sublist from a longer list and replaces it with a user-defined placeholder at the respective position.
    :param full_list: the larger list to modify
    :param partial_list: the sublist to be replaced
    :param placeholder: a user-defined placeholder to replace the sublist
    :return: the modified list, if replacement was successful; None otherwise.
    """
    if not full_list or not partial_list or placeholder is None:
        return full_list

    start_index = get_start_idx_for_sublist(full_list, partial_list)
    end_index = start_index + len(partial_list)

    if start_index != -1 and end_index <= len(full_list):
        modified_list = full_list[:start_index] + [placeholder] + full_list[end_index:]
        return modified_list

    return full_list


def insert_and_remove_placeholder(full_list: list, partial_list: list, placeholder):
    """
    Replaces a previously inserted placeholder in the list by a given sublist.
    :param full_list: the larger list to modify
    :param partial_list: the sublist to be re-inserted
    :param placeholder: a user-defined placeholder currently replacing the sublist
    :return: the modified list, if replacement was successful; None otherwise.
    """
    if full_list is None or partial_list is None or placeholder not in full_list:
        return None

    index = full_list.index(placeholder)
    full_list.remove(placeholder)
    full_list[index:index] = partial_list

    return full_list


def remove_repeating_symbols(l, symbol):
    """
    a method to remove subsequent repetitions of a given symbol from a list
    :param l: the list to be modified
    :param symbol: the symbol to be stripped
    :return: the sanitized list
    """
    if l is None:
        return None

    if symbol is None:
        return l

    modified_list = []

    for i, x in enumerate(l):
        if i == len(l)-1 or x != symbol or x != l[i+1]:
            modified_list.append(x)

    return modified_list


def reverse_list(l):
    if not l:
        return l

    return [l[i] for i in range(len(l) - 1, -1, -1)]
