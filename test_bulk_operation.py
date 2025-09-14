#!/usr/bin/env python3

from app.services.invite_service.types import BulkInviteOperation, InviteOperation, InviteCreate

def test_bulk_operation():
    print("Testing BulkInviteOperation...")
    
    # Test valid enum operation
    op1 = BulkInviteOperation(InviteOperation.CREATE, [])
    print(f"Valid enum operation: {op1.operation}")
    
    # Test valid string operation
    op2 = BulkInviteOperation('create', [])
    print(f"Valid string operation: {op2.operation}")
    
    # Test invalid operation
    try:
        op3 = BulkInviteOperation('invalid', [])
        print(f"Invalid operation (should not reach here): {op3.operation}")
    except Exception as e:
        print(f"Error handling works: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_bulk_operation()

