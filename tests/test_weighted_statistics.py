"""
Statistical validation tests for weighted selection functionality.

This module tests that the weighted selection algorithms produce values
with probabilities close to the designated weights over many runs.
"""

import random
import unittest
from collections import Counter
from typing import Any, Dict, List

from python_proptest import Gen, run_for_all


class TestWeightedStatistics(unittest.TestCase):
    """Test statistical properties of weighted selection."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a fixed seed for reproducible tests
        random.seed(42)

    def _generate_samples(self, generator, num_samples: int = 10000) -> List[Any]:
        """Generate many samples from a generator for statistical analysis."""
        import random

        rng = random.Random(42)  # Use fixed seed for reproducibility
        samples = []
        for _ in range(num_samples):
            # Generate directly from the generator
            shrinkable = generator.generate(rng)
            samples.append(shrinkable.value)
        return samples

    def _calculate_probabilities(self, samples: List[Any]) -> Dict[Any, float]:
        """Calculate empirical probabilities from samples."""
        counter = Counter(samples)
        total = len(samples)
        return {value: count / total for value, count in counter.items()}

    def _chi_square_test(
        self, observed: Dict[Any, int], expected: Dict[Any, float], total_samples: int
    ) -> float:
        """Calculate chi-square statistic for goodness of fit test."""
        chi_square = 0.0
        for value, expected_prob in expected.items():
            observed_count = observed.get(value, 0)
            expected_count = expected_prob * total_samples
            if expected_count > 0:
                chi_square += (observed_count - expected_count) ** 2 / expected_count
        return chi_square

    def _is_probability_close(
        self, actual: float, expected: float, tolerance: float = 0.05
    ) -> bool:
        """Check if actual probability is close to expected within tolerance."""
        return abs(actual - expected) <= tolerance

    def test_element_of_weighted_probability_distribution(self):
        """Test that Gen.element_of with weighted values produces correct probabilities."""
        # Create a generator with known weights
        char_gen = Gen.element_of(
            Gen.weighted_value("a", 0.6),  # 60%
            Gen.weighted_value("b", 0.3),  # 30%
            Gen.weighted_value("c", 0.1),  # 10%
        )

        # Generate many samples
        samples = self._generate_samples(char_gen, num_samples=10000)
        probabilities = self._calculate_probabilities(samples)

        # Check that probabilities are close to expected
        self.assertTrue(
            self._is_probability_close(probabilities.get("a", 0), 0.6),
            f"Expected 'a' probability ~0.6, got {probabilities.get('a', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("b", 0), 0.3),
            f"Expected 'b' probability ~0.3, got {probabilities.get('b', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("c", 0), 0.1),
            f"Expected 'c' probability ~0.1, got {probabilities.get('c', 0)}",
        )

        # Verify all samples are from expected values
        self.assertEqual(set(probabilities.keys()), {"a", "b", "c"})

    def test_one_of_weighted_probability_distribution(self):
        """Test that Gen.one_of with weighted generators produces correct probabilities."""
        # Create generators that produce distinct values
        gen_a = Gen.just("A")
        gen_b = Gen.just("B")
        gen_c = Gen.just("C")

        # Create weighted one_of generator
        weighted_gen = Gen.one_of(
            Gen.weighted_gen(gen_a, 0.5),  # 50%
            Gen.weighted_gen(gen_b, 0.3),  # 30%
            Gen.weighted_gen(gen_c, 0.2),  # 20%
        )

        # Generate many samples
        samples = self._generate_samples(weighted_gen, num_samples=10000)
        probabilities = self._calculate_probabilities(samples)

        # Check that probabilities are close to expected
        self.assertTrue(
            self._is_probability_close(probabilities.get("A", 0), 0.5),
            f"Expected 'A' probability ~0.5, got {probabilities.get('A', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("B", 0), 0.3),
            f"Expected 'B' probability ~0.3, got {probabilities.get('B', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("C", 0), 0.2),
            f"Expected 'C' probability ~0.2, got {probabilities.get('C', 0)}",
        )

        # Verify all samples are from expected values
        self.assertEqual(set(probabilities.keys()), {"A", "B", "C"})

    def test_mixed_weighted_unweighted_element_of(self):
        """Test probability distribution for mixed weighted/unweighted values in element_of."""
        # Create generator with one weighted and two unweighted values
        mixed_gen = Gen.element_of(
            Gen.weighted_value("X", 0.6),  # 60%
            "Y",  # 20% (remaining 40% split equally)
            "Z",  # 20% (remaining 40% split equally)
        )

        # Generate many samples
        samples = self._generate_samples(mixed_gen, num_samples=10000)
        probabilities = self._calculate_probabilities(samples)

        # Check that probabilities are close to expected
        self.assertTrue(
            self._is_probability_close(probabilities.get("X", 0), 0.6),
            f"Expected 'X' probability ~0.6, got {probabilities.get('X', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("Y", 0), 0.2),
            f"Expected 'Y' probability ~0.2, got {probabilities.get('Y', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("Z", 0), 0.2),
            f"Expected 'Z' probability ~0.2, got {probabilities.get('Z', 0)}",
        )

    def test_mixed_weighted_unweighted_one_of(self):
        """Test probability distribution for mixed weighted/unweighted generators in one_of."""
        # Create generator with one weighted and two unweighted generators
        mixed_gen = Gen.one_of(
            Gen.weighted_gen(Gen.just("P"), 0.7),  # 70%
            Gen.just("Q"),  # 15% (remaining 30% split equally)
            Gen.just("R"),  # 15% (remaining 30% split equally)
        )

        # Generate many samples
        samples = self._generate_samples(mixed_gen, num_samples=10000)
        probabilities = self._calculate_probabilities(samples)

        # Check that probabilities are close to expected
        self.assertTrue(
            self._is_probability_close(probabilities.get("P", 0), 0.7),
            f"Expected 'P' probability ~0.7, got {probabilities.get('P', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("Q", 0), 0.15),
            f"Expected 'Q' probability ~0.15, got {probabilities.get('Q', 0)}",
        )
        self.assertTrue(
            self._is_probability_close(probabilities.get("R", 0), 0.15),
            f"Expected 'R' probability ~0.15, got {probabilities.get('R', 0)}",
        )

    def test_all_unweighted_element_of(self):
        """Test that all unweighted values get equal probability in element_of."""
        # Create generator with all unweighted values
        equal_gen = Gen.element_of("A", "B", "C", "D")

        # Generate many samples
        samples = self._generate_samples(equal_gen, num_samples=10000)
        probabilities = self._calculate_probabilities(samples)

        # Check that all probabilities are close to 0.25 (1/4)
        for value in ["A", "B", "C", "D"]:
            self.assertTrue(
                self._is_probability_close(probabilities.get(value, 0), 0.25),
                f"Expected '{value}' probability ~0.25, got {probabilities.get(value, 0)}",
            )

    def test_all_unweighted_one_of(self):
        """Test that all unweighted generators get equal probability in one_of."""
        # Create generator with all unweighted generators
        equal_gen = Gen.one_of(
            Gen.just("W"), Gen.just("X"), Gen.just("Y"), Gen.just("Z")
        )

        # Generate many samples
        samples = self._generate_samples(equal_gen, num_samples=10000)
        probabilities = self._calculate_probabilities(samples)

        # Check that all probabilities are close to 0.25 (1/4)
        for value in ["W", "X", "Y", "Z"]:
            self.assertTrue(
                self._is_probability_close(probabilities.get(value, 0), 0.25),
                f"Expected '{value}' probability ~0.25, got {probabilities.get(value, 0)}",
            )

    def test_chi_square_goodness_of_fit(self):
        """Test using chi-square statistic for goodness of fit."""
        # Create a generator with known weights
        gen = Gen.element_of(
            Gen.weighted_value(1, 0.4),  # 40%
            Gen.weighted_value(2, 0.3),  # 30%
            Gen.weighted_value(3, 0.2),  # 20%
            Gen.weighted_value(4, 0.1),  # 10%
        )

        # Generate samples
        num_samples = 10000
        samples = self._generate_samples(gen, num_samples=num_samples)
        observed_counts = Counter(samples)

        # Expected probabilities
        expected_probs = {1: 0.4, 2: 0.3, 3: 0.2, 4: 0.1}

        # Calculate chi-square statistic
        chi_square = self._chi_square_test(observed_counts, expected_probs, num_samples)

        # For 3 degrees of freedom (4 categories - 1), critical value at 95% is ~7.81
        # We expect chi-square to be much lower for a good fit
        self.assertLess(
            chi_square,
            20.0,
            f"Chi-square statistic {chi_square} is too high, indicating poor fit",
        )

    def test_edge_case_single_weighted_value(self):
        """Test edge case with single weighted value."""
        gen = Gen.element_of(Gen.weighted_value("only", 1.0))

        samples = self._generate_samples(gen, num_samples=1000)
        probabilities = self._calculate_probabilities(samples)

        # Should always generate 'only'
        self.assertEqual(probabilities.get("only", 0), 1.0)
        self.assertEqual(len(probabilities), 1)

    def test_edge_case_single_weighted_generator(self):
        """Test edge case with single weighted generator."""
        gen = Gen.one_of(Gen.weighted_gen(Gen.just("single"), 1.0))

        samples = self._generate_samples(gen, num_samples=1000)
        probabilities = self._calculate_probabilities(samples)

        # Should always generate 'single'
        self.assertEqual(probabilities.get("single", 0), 1.0)
        self.assertEqual(len(probabilities), 1)


if __name__ == "__main__":
    unittest.main()
