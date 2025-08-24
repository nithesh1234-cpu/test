#!/usr/bin/env python3

import sys


def parse_numbers_from_args(argument_values: list[str]) -> list[float]:
    numbers: list[float] = []
    for value in argument_values:
        try:
            numbers.append(float(value))
        except ValueError:
            raise SystemExit(f"Invalid number: {value}")
    return numbers


def parse_numbers_from_stdin() -> list[float]:
    try:
        user_input = input("Enter numbers separated by spaces (or commas): ").strip()
    except EOFError:
        return []

    if not user_input:
        return []

    normalized = user_input.replace(',', ' ')
    tokens = [token for token in normalized.split(' ') if token]
    numbers: list[float] = []
    for token in tokens:
        try:
            numbers.append(float(token))
        except ValueError:
            raise SystemExit(f"Invalid number: {token}")
    return numbers


def print_number_compact(value: float) -> None:
    if value.is_integer():
        print(int(value))
    else:
        print(value)


def main() -> None:
    args = sys.argv[1:]
    numbers = parse_numbers_from_args(args) if args else parse_numbers_from_stdin()

    if not numbers:
        print(0)
        return

    result = sum(numbers)
    print_number_compact(result)


if __name__ == "__main__":
    main()

