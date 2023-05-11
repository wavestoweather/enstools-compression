"""
Functions to find which bits contain relevant information
using the approach described in Klöwer et al. 2021
(https://doi.org/10.1038/s43588-021-00156-2)

"""

import numpy as np
import xarray
from scipy.stats import binom
from enstools.io import read


def get_uint_type_by_bit_length(bits: int) -> type:
    """
    Returns the numpy data type that corresponds to a unsigned integer with a certain number of bits.
    """
    if bits == 8:
        return np.uint8
    if bits == 16:
        return np.uint16
    if bits == 32:
        return np.uint32
    if bits == 64:
        return np.uint64
    raise NotImplementedError(f"mask_generator does not have this number of bits implemented: {bits}")


def mask_generator(bits: int = 32, ones: int = 9):
    """
    This function returns a mask of type unsigned int, which has the number of bits specified by the input variable bits
    and has the number of ones specified by the input variable ones.

    Example:
        mask_generator(32,10) would return an unsigned integer whose binary
        representation would be 11111111110000000000000000000000

    FIXME: Right now we are not even considering little-big endian and these stuff.

    """
    mask_type = get_uint_type_by_bit_length(bits)
    # The approach to generate the mask is to generate a different single bit masks for each position that has a one
    # and then just merge them using logical_or
    elements = [single_bit_mask(position=i, bits=bits) for i in range(ones)]

    mask = mask_type(0.)
    for element in elements:
        mask = np.bitwise_or(mask, element)

    return mask_type(mask)


def single_bit_mask(position: int = 0, bits: int = 32):
    """
    It generates a mask that has a single 1 to the specified position.
    """
    # Get corresponding uint type
    mask_type = get_uint_type_by_bit_length(bits)
    # Get a 1 from the proper type
    mask = mask_type(1)
    # Shift 1 to the proper position
    shift = mask_type(bits - position - 1)
    shifted = np.left_shift(mask, shift, casting="unsafe")
    return mask_type(shifted)


def apply_mask(array: np.array, mask: np.integer) -> np.array:
    """
    Apply the mask to a given array.
    """
    # Get number of bits
    bits = array.itemsize * 8

    # Get the corresponding integer type
    int_type = get_uint_type_by_bit_length(bits)

    # Get a view of the array as the corresponding uint type.
    i_array = array.view(dtype=int_type)

    # Apply mask
    masked_array = np.bitwise_and(i_array, mask)

    # Return the masked array with the proper type.
    return masked_array.view(array.dtype)


def extract_bit_at_position(array: np.array, position: int) -> np.array:
    """
    Extracts the bit at the specified position from each value in the input array.

    Args:
        array (np.array): The input array.
        position (int): The position of the bit to extract (0-indexed).

    Returns:
        np.array: An array where each value represents the bit at the specified position.

    Raises:
        AssertionError: If the input array is not one-dimensional (1D).
    """

    assert array.ndim == 1

    # Calculate the number of bits per value (equal to the array type size in bytes multiplied by 8)
    byte_length = array.dtype.itemsize
    bits = byte_length * 8

    # Calculate the number of bits to shift to bring the desired bit to the least significant bit
    shift = bits - position - 1

    # Calculate the bit mask for the specified position
    mask = single_bit_mask(position=position, bits=bits)

    # Apply the mask to the array, retaining only the bit at the specified position
    masked_array = np.bitwise_and(array.view(dtype=mask.dtype), mask)

    # Right-shift the masked values to bring the desired bit to the least significant bit
    masked_array = np.right_shift(masked_array, shift)

    return np.uint8(masked_array)


# TODO: Need to better document and explain what these functions are, I don't even remember myself what it is.
def calculate_entropy(probabilities: list) -> float:
    """
    Calculates the entropy of a list of probabilities

    Args:
        probabilities (list): The list of probabilities of each bit.

    Returns:
        float: The entropy value.
    """
    entropy_sum = 0.0  # Initialize the entropy sum
    zero_threshold = 0.0  # Initialize the zero threshold

    for probability in probabilities:
        if probability > zero_threshold:
            # Calculate the contribution to entropy only for non-zero probabilities
            entropy_sum += probability * np.log(probability)

    entropy = -entropy_sum if entropy_sum < 0 else entropy_sum
    return entropy


def calculate_normalized_entropy(probabilities: list, base: float) -> float:
    """
    Calculates the normalized entropy of a probability distribution.

    The normalized entropy is obtained by dividing the entropy of the probability distribution by the logarithm
    of the specified base.

    Args:
        probabilities (iterable): The probability distribution.
        base (float): The logarithmic base for normalization.

    Returns:
        float: The normalized entropy value.

    """
    entropy = calculate_entropy(probabilities)
    logarithm_base = np.log(base)
    normalized_entropy = entropy / logarithm_base

    return normalized_entropy


def bit_conditional_count(array: np.array) -> np.array:
    """
    Calculates the conditional count of bit patterns in the given array.

    Args:
        array (np.array): The input array.

    Returns:
        np.array: The count matrix of bit patterns.

    """

    # Function for logical negation
    logical_not = np.logical_not

    # Convert the input array to a boolean array
    array_bool = array.astype(bool)

    # Shift the boolean array circularly by one position to the right
    rolled_bool = np.roll(array_bool, 1)

    # Calculate different bit pattern combinations
    zero_zero = np.logical_and(logical_not(array_bool), logical_not(rolled_bool))
    zero_one = np.logical_and(logical_not(array_bool), rolled_bool)
    one_zero = np.logical_and(array_bool, logical_not(rolled_bool))
    one_one = np.logical_and(array_bool, rolled_bool)

    # Initialize the count matrix
    count_matrix = np.zeros(shape=(2, 2))

    # Calculate counts of each bit pattern and assign to the count matrix
    count_matrix[0, 0] = np.sum(zero_zero)
    count_matrix[0, 1] = np.sum(zero_one)
    count_matrix[1, 0] = np.sum(one_zero)
    count_matrix[1, 1] = np.sum(one_one)

    return count_matrix


def calculate_bit_mutual_information(array: np.array) -> float:
    """
    Calculates the mutual information between bits in the given array.

    Mutual information measures the statistical dependence or correlation between bits.

    Args:
        array (np.array): The input array.

    Returns:
        float: The mutual information value.

    """

    # Calculate the conditional count of bit patterns in the array
    counter = bit_conditional_count(array)

    # Calculate the probabilities of each bit pattern
    probabilities = counter / array.size

    # Calculate the probabilities of having a bit value of 0 and 1
    bit_1_probabilities = np.sum(array) / array.size
    bit_0_probabilities = 1.0 - bit_1_probabilities

    # Initialize the conditional probability matrix
    conditional_probabilities = np.zeros(shape=(2, 2))

    # Calculate the conditional probabilities based on the bit value probabilities
    conditional_probabilities[0, 0] = (probabilities[0, 0] / bit_0_probabilities) if bit_0_probabilities > 0.0 else 0.0
    conditional_probabilities[0, 1] = (probabilities[0, 1] / bit_0_probabilities) if bit_0_probabilities > 0.0 else 0.0
    conditional_probabilities[1, 0] = (probabilities[1, 0] / bit_1_probabilities) if bit_1_probabilities > 0.0 else 0.0
    conditional_probabilities[1, 1] = (probabilities[1, 1] / bit_1_probabilities) if bit_1_probabilities > 0.0 else 0.0

    # Calculate the entropies
    entropy_0 = (-((conditional_probabilities[0, 0] * np.log2(conditional_probabilities[0, 0]))
                   if conditional_probabilities[0, 0] > 0.0 else 0.0)
                 - ((conditional_probabilities[0, 1] * np.log2(conditional_probabilities[0, 1]))
                    if conditional_probabilities[0, 1] > 0.0 else 0.0)
                 )

    entropy_1 = (-((conditional_probabilities[1, 0] * np.log2(conditional_probabilities[1, 0]))
                   if conditional_probabilities[1, 0] > 0.0 else 0.0)
                 - ((conditional_probabilities[1, 1] * np.log2(conditional_probabilities[1, 1]))
                    if conditional_probabilities[1, 1] > 0.0 else 0.0)
                 )

    # Calculate the overall entropy
    overall_entropy = calculate_normalized_entropy([bit_0_probabilities, bit_1_probabilities], 2)

    # Calculate the mutual information
    mutual_information = overall_entropy - bit_0_probabilities * entropy_0 - bit_1_probabilities * entropy_1

    # If the mutual information is negative, set it to 0
    if mutual_information < 0:
        mutual_information = 0

    return mutual_information


def array_mutual_information(array: np.array) -> list:
    """
    Calculates the mutual information for each bit position in the given array.
    Returns a list of the mutual information values for each bit position.

    Args:
        array (np.array): The input array.

    Returns:
        list: The mutual information values for each bit position.

    """

    # Calculate the number of bits in each element of the array
    bit_length = array.itemsize * 8

    # Initialize an array to store the mutual information for each bit position
    mutual_information = np.zeros(shape=bit_length, dtype=np.float32)

    # Iterate over each bit position
    for position in range(bit_length):
        # Extract the bit at the current position from the array
        bits = extract_bit_at_position(array, position=position)

        # Calculate the mutual information for the extracted bits
        mutual_information[position] = calculate_bit_mutual_information(bits)

    # Filter out insignificant mutual information values based on the size of the original array
    filtered_mutual_information = filter_insignificant_values(mutual_information, array.size)

    return filtered_mutual_information


def filter_insignificant_values(mutual_information_list: list, number_of_elements: int) -> list:
    """
    Filters out insignificant mutual information values from the given list.

    Insignificant values are identified based on a predefined threshold.

    Args:
        mutual_information_list (list): The list of mutual information values.
        number_of_elements (int): The number of elements in the original array.

    Returns:
        list: The filtered mutual information values.

    """

    # FIXME: The code below is a placeholder and needs to be replaced with the appropriate implementation
    # In the code created by the author of the paper, they use the following logic:
    # if set_zero_insignificant:
    #     p = binom_confidence(N, confidence)  # Get chance p for 1 (or 0) from binomial distribution
    #     I₀ = 1 - entropy([p, 1-p], 2)        # Calculate the free entropy of a random [bit]
    #     I[I .<= I₀] .= 0                     # Set insignificant values to zero
    # end

    # FIXME: Replace the line below with the actual implementation
    threshold_information = minimum_meaningful_value(number_of_elements)

    # Filter out insignificant mutual information values
    filtered_mi = [v if v > threshold_information else 0.0 for v in mutual_information_list]

    return filtered_mi


def binom_confidence(number_of_elements: int, confidence: float) -> float:
    """
    Calculates the confidence threshold for binomial distribution.

    The threshold is calculated based on the given number of elements and confidence level.

    Args:
        number_of_elements (int): The number of elements in the distribution.
        confidence (float): The desired confidence level.

    Returns:
        float: The confidence threshold.

    """

    # Calculate the confidence threshold using the inverse cumulative distribution function (ppf)
    threshold = binom.ppf(confidence, number_of_elements, 0.5) / number_of_elements

    return threshold


def minimum_meaningful_value(number_of_elements: int, confidence: float = 0.99) -> float:
    """
    Calculates the minimum meaningful value based on the number of elements and confidence level.

    The minimum meaningful value represents a threshold below which
    the mutual information values are considered insignificant.

    Args:
        number_of_elements (int): The number of elements in the distribution.
        confidence (float, optional): The desired confidence level. Defaults to 0.99.

    Returns:
        float: The minimum meaningful value.

    """

    # Calculate the confidence threshold using the binom_confidence function
    probability = binom_confidence(number_of_elements=number_of_elements, confidence=confidence)

    # Calculate the entropy of a random [bit]
    entropy = calculate_normalized_entropy([probability, 1 - probability], 2)

    # Calculate the minimum meaningful value
    minimum_meaningful = 1.0 - entropy

    return minimum_meaningful


def analyze_file_significant_bits(file_path: str) -> dict:
    """
    Analyzes the significant bits in each variable of a file.

    Reads the file, analyzes each variable, and returns a dictionary
    with the number of significant bits for each variable.

    Args:
        file_path (str): The path to the file.

    Returns:
        dict: A dictionary with variable names as keys and the number of significant bits as values.

    """

    # Open the file using enstools.io read function
    dataset = read(file_path)

    # Get the list of variables from the dataset
    variables = [var for var in dataset.variables if var not in dataset.coords]

    # Analyze each variable and store the results in a dictionary
    results = {}
    for variable in variables:
        # Analyze the significant bits of the variable
        _, _, nsb = analyze_variable_significant_bits(dataset[variable])
        results[variable] = nsb

    return results


def analyze_variable_significant_bits(data_array: xarray.DataArray):
    """
    Analyzes the significant bits in a variable's data.

    Calculates the mutual information between frames and performs a comparison to identify significant variability.

    Args:
        data_array (xr.DataArray): The input data array.

    Returns:
        tuple: A tuple containing the exponent information, mantissa information, and number of significant bits.

    """

    # Squeeze the data array to remove dimensions of size 1
    data_array = data_array.squeeze()

    # Ensure the array has at least 3 dimensions
    assert data_array.ndim >= 3

    # Extract the first and last frames for analysis
    first_frame_data = data_array[0].values.ravel()
    last_frame_data = data_array[-1].values.ravel()

    # Apply fix for repetition
    first_frame_data = fix_repetition(first_frame_data)
    last_frame_data = fix_repetition(last_frame_data)

    # Calculate mutual information for the first and last frames
    first_frame_mi = array_mutual_information(first_frame_data)
    last_frame_mi = array_mutual_information(last_frame_data)

    # Sum all information
    first_frame_total_information = np.sum(first_frame_mi)
    last_frame_total_information = np.sum(last_frame_mi)

    # Check if there is significant variability between the first and last frames
    if np.abs(first_frame_total_information - last_frame_total_information) > 0.5:
        print("Warning, first frame is unreliable, checking all data")
        max_info = max(first_frame_total_information, last_frame_total_information)
        max_mutual_info = first_frame_mi
        for frame in data_array:
            frame_data = frame.values.ravel()
            frame_data = fix_repetition(frame_data)
            temporal_mutual_information = array_mutual_information(frame_data)
            if sum(temporal_mutual_information) >= max_info:
                max_info = sum(temporal_mutual_information)
                max_mutual_info = temporal_mutual_information
        first_frame_mi = max_mutual_info

    # Calculate exponent information, mantissa information, and the number of significant bits
    exponent_information, mantissa_information, number_of_significant_bits = \
        mutual_information_report(first_frame_mi, first_frame_data.size)

    return exponent_information, mantissa_information, number_of_significant_bits


def mutual_information_report(mutual_information_list: list, number_of_elements: int):
    """
    Analyzes the mutual information list and calculates the exponent information, mantissa information,
    and the number of significant bits.

    Args:
        mutual_information_list (list): The list of mutual information values.
        number_of_elements (int): The total number of elements.

    Returns:
        tuple: A tuple containing the exponent information, mantissa information, and the number of significant bits.

    """

    bits = len(mutual_information_list)

    # Define the first mantissa bit based on the total number of bits
    if bits == 32:
        first_mantissa_bit = 10
    elif bits == 64:
        first_mantissa_bit = 12
    else:
        raise NotImplementedError

    # Define the slices for exponent and mantissa bits
    exponent = slice(1, first_mantissa_bit)
    mantissa = slice(first_mantissa_bit, bits)

    # Get exponent bits and calculate total information in exponent bits
    exponent_information = sum(mutual_information_list[exponent])

    # Get mantissa bits
    mantissa_bits = mutual_information_list[mantissa]

    # Remove information below the threshold
    threshold = minimum_meaningful_value(number_of_elements)
    mantissa_bits = [bit_information if bit_information >= threshold else 0.0 for bit_information in mantissa_bits]

    # Calculate total information from the mantissa bits
    mantissa_information = sum(mantissa_bits)

    # Set the percentage of information to preserve
    preserved_information_pct = 0.99
    preserved_information_threshold = mantissa_information * preserved_information_pct

    # Calculate accumulated information up to a certain bit
    accumulated = [mantissa_bits[0]]
    for bit_information in mantissa_bits[1:]:
        accumulated.append(accumulated[-1] + bit_information)

    accumulated_over_threshold = [bit_info > preserved_information_threshold for bit_info in accumulated]

    # Get the number of significant mantissa bits that fulfill the defined threshold
    number_of_significant_mantissa_bits = accumulated_over_threshold.index(True)
    number_of_significant_bits = first_mantissa_bit + number_of_significant_mantissa_bits

    return exponent_information, mantissa_information, number_of_significant_bits


def fix_repetition(array: np.array) -> np.array:
    """
    Removes consecutive repeated values from a numpy array.

    This function takes a numpy array as input and returns the same array without consecutive values that are repeated.

    Args:
        array (np.array): The input numpy array.

    Returns:
        np.array: The array without consecutive repeated values.

    """

    # Shift the array by one position to compare with the original array
    shifted = np.roll(array, 1)

    # Find the indices where the values are not equal to their previous values
    indices = array != shifted

    # Return the array without consecutive repeated values
    return array[indices]
