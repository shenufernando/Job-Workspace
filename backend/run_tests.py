import pytest
import sys
with open('pytest_out.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    pytest.main(['-v', 'tests'])
    sys.stdout = sys.__stdout__
