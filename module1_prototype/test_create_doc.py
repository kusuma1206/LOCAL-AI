import sys
sys.path.append('.')
from processing.storage import create_document
print(create_document('Zero Trust AI Architecture', 'zero_trust.md'))
