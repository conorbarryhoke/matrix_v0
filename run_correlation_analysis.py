#!/usr/bin/env python3
"""
Execute the correlation analysis notebook.

This script runs the correlation_analysis.ipynb notebook and saves the results
back to the same file with all outputs included.
"""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import sys
from pathlib import Path

def main():
    notebook_path = Path(__file__).parent / 'notebooks' / 'correlation_analysis.ipynb'

    print(f"Reading notebook: {notebook_path}")

    # Read notebook
    with open(notebook_path, 'r') as f:
        nb = nbformat.read(f, as_version=4)

    print("Executing notebook (this may take a few minutes)...")

    # Execute
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    try:
        ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})
    except Exception as e:
        print(f"❌ Error executing notebook: {e}", file=sys.stderr)
        sys.exit(1)

    # Save with outputs
    print(f"Saving results to: {notebook_path}")
    with open(notebook_path, 'w') as f:
        nbformat.write(nb, f)

    print('✅ Correlation analysis completed successfully!')
    print(f'   Results saved to: {notebook_path}')

if __name__ == '__main__':
    main()
