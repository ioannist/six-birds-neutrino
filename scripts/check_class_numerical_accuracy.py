#!/usr/bin/env python3
"""CLASS-only entry point for sampled Boltzmann numerical sensitivity controls."""
from check_boltzmann_numerical_accuracy import main


if __name__ == '__main__':
    main(required_backend='classy')
