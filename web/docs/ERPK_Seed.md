<!-- ABOUTME: Help documentation for the ERPK Seed node. -->
<!-- ABOUTME: Generates a seed value with optional range clamping for reproducibility. -->

# Seed

Generates a seed value that can be connected to any node's seed input. Useful for sharing a single seed across multiple API nodes or constraining seeds to a specific range.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| seed | Int | 0 | Seed value with randomize/fixed/increment/decrement control |
| min_value | Int | 0 | Minimum seed value (optional). Output is clamped to this lower bound |
| max_value | Int | 2147483647 | Maximum seed value (optional). Output is clamped to this upper bound |

## Output

| Output | Type | Description |
|--------|------|-------------|
| seed | INT | The seed value, clamped to the specified range |

## Notes

- Use the control dropdown (randomize/fixed/increment/decrement) to control how the seed changes between queue runs
- Connect the output to multiple nodes to share the same seed across your workflow
- Set min_value and max_value to constrain seeds to a specific range
