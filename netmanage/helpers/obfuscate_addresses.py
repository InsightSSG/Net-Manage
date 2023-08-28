#!/usr/bin/env python3

"""
IP and Subnet Transformation Module.

This module provides functionality to tokenize IP addresses and subnets while
retaining their format and ensuring referential integrity. It supports IP
addresses, CIDR notation, and IP + Subnet mask format. The offset used for
transformation is a required parameter for all transformation functions.

Functions:
    - ip_to_int: Converts an IP address string to an integer.
    - int_to_ip: Converts an integer to an IP address string.
    - transform_ip: Transforms an IP address using a specified offset.
    - reverse_transform_ip: Reverses the transformation of an IP address.
    - transform_subnet: Transforms a subnet (CIDR or IP + Subnet mask).
    - reverse_transform_subnet: Reverses the transformation of a subnet.
    - test_module: Tests the functionality of the module using examples.

Example:
    >>> transform_ip("192.168.1.1", 98765432)
    '197.89.9.141'
    >>> reverse_transform_ip("197.89.9.141", 98765432)
    '192.168.1.1'
    >>> transform_subnet("192.168.1.0/24", 98765432)
    '197.89.9.140/8'
    >>> reverse_transform_subnet("197.89.9.140/8", 98765432)
    '192.168.1.0/24'
"""

import argparse
import ipaddress

# Set up argument parser
parser = argparse.ArgumentParser(
    description='Tokenize IP addresses and subnets while retaining format.')
parser.add_argument('-i', '--ip_addresses',  # nargs='+',
                    help='''Comma-delimited list of IP addresses (with or
                            without CIDR or subnet mask) to be tested, wrapped
                            in quotes.''')
parser.add_argument('-o', '--offset', type=int,
                    help='Offset used for transformations.')

# Parse the arguments
args = parser.parse_args()

# Use parsed arguments if provided, else use defaults
print(args.ip_addresses)
ip_addresses_to_test = [_.strip() for _ in args.ip_addresses.split(',')] \
    if args.ip_addresses else [
    "66.119.107.6", "10.10.100.10/25", "172.21.243.18 255.255.255.0"]
offset_to_use = args.offset if args.offset else 98765432


def ip_to_int(ip: str) -> int:
    """
    Convert an IP address string to its corresponding integer representation.

    Parameters
    ----------
    ip : str
        The IP address in string format.

    Returns
    -------
    int
        The integer representation of the IP address.
    """
    return int(ipaddress.ip_address(ip))


def int_to_ip(val: int) -> str:
    """
    Convert an integer to its corresponding IP address representation.

    Parameters
    ----------
    val : int
        The integer value representing an IP address.

    Returns
    -------
    str
        The IP address in string format.
    """
    return str(ipaddress.ip_address(val & 0xFFFFFFFF))  # Ensure <= 32 bits.


def transform_ip(ip: str, offset: int) -> str:
    """
    Transform an IP address using a specified offset.

    Parameters
    ----------
    ip : str
        The original IP address to be transformed.
    offset : int
        The offset used for transformation.

    Returns
    -------
    str
        The transformed IP address.
    """
    ip_int = ip_to_int(ip)
    # Wrap around within the 32-bit range
    transformed_int = (ip_int + offset) % (2**32)
    return int_to_ip(transformed_int)


def reverse_transform_ip(transformed_ip: str, offset: int) -> str:
    """
    Reverse the transformation applied to an IP address.

    Parameters
    ----------
    transformed_ip : str
        The transformed IP address.
    offset : int
        The offset used for original transformation.

    Returns
    -------
    str
        The original IP address.
    """
    transformed_int = ip_to_int(transformed_ip)
    # Wrap around within the 32-bit range
    original_int = (transformed_int - offset) % (2**32)
    return int_to_ip(original_int)


def transform_subnet(subnet: str, offset: int) -> str:
    """
    Transform a subnet mask or CIDR notation.

    The function checks if the input is in CIDR format or plain subnet mask
    and applies the appropriate transformation.

    Parameters
    ----------
    subnet : str
        The original subnet in CIDR notation or as a subnet mask.
    offset : int
        The offset used for transformation.

    Returns
    -------
    str
        The transformed subnet in the same format as the input.
    """
    if "/" in subnet:  # Check if it's in CIDR format
        ip, prefix_length = subnet.split("/")
        transformed_ip = transform_ip(ip, offset)
        transformed_prefix_length = (
            int(prefix_length) + 16) % 32  # Shift by 16, wrap at 32
        return f"{transformed_ip}/{transformed_prefix_length}"
    else:  # Treat as a plain subnet mask
        transformed_mask = transform_ip(subnet, offset)
        return transformed_mask


def reverse_transform_subnet(transformed_subnet: str, offset: int) -> str:
    """
    Reverse the transformation applied to a subnet mask or CIDR notation.

    The function checks the format of the input and applies the appropriate
    reversal transformation.

    Parameters
    ----------
    transformed_subnet : str
        The transformed subnet in CIDR notation or as a subnet mask.
    offset : int
        The offset used for original transformation.

    Returns
    -------
    str
        The original subnet in the same format as the input.
    """
    if "/" in transformed_subnet:
        ip, prefix_length = transformed_subnet.split("/")
        original_ip = reverse_transform_ip(ip, offset)
        # Shift back by 16, wrap at 32
        original_prefix_length = (int(prefix_length) - 16) % 32
        return f"{original_ip}/{original_prefix_length}"
    else:
        original_mask = reverse_transform_ip(transformed_subnet, offset)
        return original_mask


def test_module(ip_addresses=["66.119.107.6",
                              "10.10.100.10/25",
                              "172.21.243.18 255.255.255.0"],
                offset=98765432):
    """
    Test the functionality of the module using various examples.

    This function performs transformations and reversals on a set of provided
    IP addresses to validate the module's functionality.

    Parameters
    ----------
    ip_addresses : list, optional
        A list of IP addresses (with or without CIDR or subnet mask) to
Returns
-------
None

Prints
------
str
    Validation results for each IP address tested.
"""
    for value in ip_addresses:
        is_valid = False
        if "/" in value:
            transformed_value = transform_subnet(value, offset)
            reversed_value = reverse_transform_subnet(transformed_value,
                                                      offset)
            is_valid = (value == reversed_value)
        elif " " in value:
            ip, subnet_mask = value.split(" ")
            transformed_ip = transform_ip(ip, offset)
            transformed_mask = transform_subnet(subnet_mask, offset)
            reversed_ip = reverse_transform_ip(transformed_ip, offset)
            reversed_mask = reverse_transform_subnet(transformed_mask, offset)
            transformed_value = f"{transformed_ip} {transformed_mask}"
            reversed_value = f"{reversed_ip} {reversed_mask}"
            is_valid = (value == reversed_value)
        else:
            transformed_value = transform_ip(value, offset)
            reversed_value = reverse_transform_ip(transformed_value, offset)
            is_valid = (value == reversed_value)

        output = [f"Original: {value},",
                  f"Transformed: {transformed_value},",
                  f"Reversed: {reversed_value},",
                  f"Valid: {is_valid},"]
        output = ' '.join(output)
        print(output)


# Call the test_module function with the specified or default parameters
if __name__ == '__main__':
    test_module(ip_addresses=ip_addresses_to_test, offset=offset_to_use)
